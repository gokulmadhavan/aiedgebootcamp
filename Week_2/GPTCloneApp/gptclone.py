import streamlit as st
import google.generativeai as genai

# Page configuration
st.set_page_config(page_title="Matrix Gemini Chat", layout="wide")

# Function to add matrix background
def add_bg_from_local():
    """
    Create Matrix-style raining code background CSS
    """
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(
                rgba(0, 0, 0, 0.7), 
                rgba(0, 0, 0, 0.7)
            ), url("https://i.gifer.com/39Cg.gif");
            background-size: cover;
        }}
        .stTextInput, .stButton, input, textarea {{
            background-color: rgba(0, 0, 0, 0.5) !important;
            color: #00FF41 !important;
            border-color: #00FF41 !important;
        }}
        h1, h2, h3, p, .stMarkdown {{
            color: #00FF41 !important;
        }}
        .chat-message {{
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            color: #00FF41;
        }}
        .chat-message.user {{
            background-color: rgba(0, 100, 0, 0.3);
            border: 1px solid #00FF41;
        }}
        .chat-message.bot {{
            background-color: rgba(0, 0, 0, 0.5);
            border: 1px solid #00FF41;
        }}
        .chat-message .message {{
            flex-grow: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Add the custom background
add_bg_from_local()

# App title
st.markdown("<h1 style='text-align: center;'>Matrix Gemini Chat</h1>", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.container():
        st.markdown(f"""
        <div class="chat-message {message['role']}">
            <div class="message">{message['content']}</div>
        </div>
        """, unsafe_allow_html=True)

# Configure Gemini API using secrets
try:
    # Get API key from secrets.toml
    api_key = st.secrets["gemini"]["api_key"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"""
    Error accessing API key. Make sure you have set up your secrets.toml file correctly.
    
    Error details: {str(e)}
    """)
    st.stop()

# Function to get response from Gemini
def get_gemini_response(user_input):
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Create a prompt with instructions to keep response under 100 words
        prompt = f"""
        User query: {user_input}
        
        Important: Your response must be strictly less than 100 words.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except genai.types.generation_types.BlockedPromptException:
        return "I apologize, but I cannot process that request."
    except Exception as e:
        st.error("An error occurred while processing your request. Please try again.")
        return "I encountered an error processing your request. Please try again."

# User input area
user_input = st.text_input("Your message:", key="user_input")

# Process the input when submitted
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Show user message in chat container
    with st.container():
        st.markdown(f"""
        <div class="chat-message user">
            <div class="message">{user_input}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Get and display the response
    with st.spinner("Thinking..."):
        response = get_gemini_response(user_input)
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "bot", "content": response})
    
    # Show assistant response
    with st.container():
        st.markdown(f"""
        <div class="chat-message bot">
            <div class="message">{response}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Clear the input box
    st.session_state.user_input = ""
    st.experimental_rerun()