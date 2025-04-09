import streamlit as st
import google.generativeai as genai

# Page configuration
st.set_page_config(page_title="Matrix Gemini Chat", layout="wide")

# Function to add proper Matrix-style background
def add_matrix_bg():
    """
    Create Matrix-style raining code background CSS with custom digital rain effect
    """
    matrix_style = """
    <style>
    /* Matrix Digital Rain effect */
    .stApp {
        position: relative;
        background-color: #000000;
    }
    
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("https://media.giphy.com/media/E3y79zUo6BgKk/giphy.gif");
        background-size: cover;
        opacity: 0.5;
        z-index: -1;
    }
    
    /* Matrix-style UI elements */
    .stTextInput, .stButton>button, input, textarea {
        background-color: rgba(0, 10, 0, 0.7) !important;
        color: #00FF41 !important;
        border-color: #00FF41 !important;
    }
    
    .stTextInput>div>div>input {
        color: #00FF41 !important;
    }
    
    h1, h2, h3, p, .stMarkdown {
        color: #00FF41 !important;
        text-shadow: 0 0 5px #00FF41;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        color: #00FF41;
    }
    
    .chat-message.user {
        background-color: rgba(0, 100, 0, 0.3);
        border: 1px solid #00FF41;
        box-shadow: 0 0 5px #00FF41;
    }
    
    .chat-message.bot {
        background-color: rgba(0, 0, 0, 0.7);
        border: 1px solid #00FF41;
        box-shadow: 0 0 5px #00FF41;
    }
    
    .chat-message .message {
        flex-grow: 1;
    }
    </style>
    """
    st.markdown(matrix_style, unsafe_allow_html=True)

# Add the custom Matrix background
add_matrix_bg()

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
    except Exception as e:
        return f"Error: {str(e)}"

# Function to handle form submission
def handle_input():
    user_message = st.session_state.user_message
    if user_message:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        # Get and display the response
        with st.spinner("Thinking..."):
            response = get_gemini_response(user_message)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "bot", "content": response})
        
        # Clear input (using this method avoids the error)
        st.session_state.user_message = ""

# Initialize input field state if not exists
if "user_message" not in st.session_state:
    st.session_state.user_message = ""

# Create input form
with st.form(key="message_form", clear_on_submit=True):
    st.text_input(
        "Your message:", 
        key="user_message",
        placeholder="Ask me anything..."
    )
    submit_button = st.form_submit_button(label="Send", on_click=handle_input)

# Add a Matrix-themed footer
st.markdown(
    """
    <div style="text-align: center; color: #00FF41; margin-top: 30px; font-family: 'Courier New', monospace;">
    <p>Follow the white rabbit...</p>
    </div>
    """, 
    unsafe_allow_html=True
)