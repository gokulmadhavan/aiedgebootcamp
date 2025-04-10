import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import os
import time

# Set page configuration
st.set_page_config(page_title="LangChain Chatbot", page_icon="🤖", layout="wide")

# Add some custom CSS
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
    }
    .chat-message.user {
        background-color: #2b313e
    }
    .chat-message.bot {
        background-color: #475063
    }
    .chat-message .message {
        width: 100%; padding-left: 1rem
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if "conversation_memory" not in st.session_state:
    st.session_state.conversation_memory = ConversationBufferMemory(return_messages=True)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_initialized" not in st.session_state:
    st.session_state.gemini_initialized = False
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
if "summary_displayed" not in st.session_state:
    st.session_state.summary_displayed = False
if "last_message_time" not in st.session_state:
    st.session_state.last_message_time = 0
if "last_message" not in st.session_state:
    st.session_state.last_message = ""
if "processing_message" not in st.session_state:
    st.session_state.processing_message = False

# App title and description
st.title("🤖 LangChain Chatbot")
st.markdown("This chatbot uses LangChain with Gemini for chat and OpenAI for summarization.")

# Create two columns for API keys
col1, col2 = st.columns(2)

with col1:
    # Input for Gemini API key
    gemini_api_key = st.text_input("Enter Gemini API Key:", type="password", key="gemini_key")

with col2:
    # Input for OpenAI API key (only used at the end)
    openai_api_key = st.text_input("Enter OpenAI API Key (for summary):", type="password", key="openai_key")

# Initialize Gemini chatbot when API key is provided
if gemini_api_key and not st.session_state.gemini_initialized:
    try:
        # LangChain template for Gemini
        template = """You are a helpful, friendly AI assistant.
        
        Current conversation:
        {history}
        Human: {input}
        AI Assistant:"""
        
        PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)
        
        # Create the LangChain model
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=gemini_api_key,
            temperature=0.7,
            convert_messages=True
        )
        
        st.session_state.chatbot = ConversationChain(
            llm=llm,
            memory=st.session_state.conversation_memory,
            prompt=PROMPT,
            verbose=True
        )
        
        st.session_state.gemini_initialized = True
        st.success("Chatbot initialized! You can start chatting.")
    except Exception as e:
        st.error(f"Error initializing Gemini: {e}")

# Function to generate summary and sentiment analysis using OpenAI
def generate_summary(chat_history, openai_key):
    try:
        # Create OpenAI LLM instance
        openai_llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=openai_key,
            temperature=0
        )
        
        # Create prompt for summarization and sentiment analysis
        chat_text = "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" for msg in chat_history])
        
        summary_prompt = f"""
        You are an expert at summarizing conversations and at sentiment analysis. Below is a conversation between a user and an AI assistant:
        
        {chat_text}
        
        1. Please summarize this conversation in under 150 words.
        2. Perform a sentiment analysis of the conversation, describing the overall tone and emotions expressed.
        
        Format your response as:
        
        SUMMARY:
        [your summary here]
        
        SENTIMENT ANALYSIS:
        [your sentiment analysis here]
        """
        
        response = openai_llm.invoke(summary_prompt)
        return response.content
    except Exception as e:
        return f"Error generating summary: {e}"

# Display chat messages from history
for message in st.session_state.chat_history:
    with st.container():
        st.markdown(f"""
        <div class="chat-message {message['role']}">
            <div class="message">{message['content']}</div>
        </div>
        """, unsafe_allow_html=True)

# Display the summary section if summary is displayed
if st.session_state.summary_displayed:
    st.markdown("---")
    st.markdown("## Conversation Summary and Analysis")
    st.write(st.session_state.summary)

# Input and End button in a row
if st.session_state.gemini_initialized and not st.session_state.summary_displayed:
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("Your message:", key="user_input")
    
    with col2:
        end_chat = st.button("End Chat", key="end_chat")
    
    # Process user input with rate limiting
    if user_input:
        current_time = time.time()
        cooldown_period = 2  # seconds between messages
        
        # Check if this is a duplicate message or if we're still in cooldown
        if (user_input == st.session_state.last_message and 
            current_time - st.session_state.last_message_time < cooldown_period):
            st.warning("Please wait a moment before sending the same message again.")
        elif st.session_state.processing_message:
            st.warning("Still processing your previous message. Please wait.")
        else:
            # Set processing flag
            st.session_state.processing_message = True
            
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Update last message tracking
            st.session_state.last_message = user_input
            st.session_state.last_message_time = current_time
            
            try:
                # Get response from LangChain model
                response = st.session_state.chatbot.predict(input=user_input)
                
                # Add bot response to chat history
                st.session_state.chat_history.append({"role": "bot", "content": response})
            except Exception as e:
                st.error(f"Error getting response: {e}")
            finally:
                # Reset processing flag
                st.session_state.processing_message = False
            
            # Force streamlit to rerun to display the new messages
            st.rerun()
    
    # End chat and generate summary
    if end_chat and openai_api_key:
        if len(st.session_state.chat_history) == 0:
            st.warning("You haven't had any conversation yet!")
        else:
            with st.spinner("Generating conversation summary..."):
                summary = generate_summary(st.session_state.chat_history, openai_api_key)
                st.session_state.summary = summary
                st.session_state.summary_displayed = True
                st.rerun()
    elif end_chat and not openai_api_key:
        st.warning("Please enter your OpenAI API key to generate a summary.")

# Restart button when chat is ended
if st.session_state.summary_displayed:
    if st.button("Start New Chat"):
        # Reset all session state
        st.session_state.conversation_memory = ConversationBufferMemory(return_messages=True)
        st.session_state.chat_history = []
        st.session_state.summary_displayed = False
        st.session_state.last_message = ""
        st.session_state.last_message_time = 0
        st.session_state.processing_message = False
        st.rerun()