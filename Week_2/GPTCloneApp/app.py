import streamlit as st
import google.generativeai as genai
import os

# Page configuration
st.set_page_config(page_title="Matrix Gemini Chat", layout="wide")

# Matrix-style CSS
st.markdown("""
<style>
body {
    background-color: #000000;
    color: #00FF41;
}

.stApp {
    background-color: #000000;
}

/* Matrix digital rain background */
.stApp::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("https://i.gifer.com/embedded/download/KMhn.gif");
    background-size: cover;
    opacity: 0.3;
    z-index: -1;
    pointer-events: none;
}

/* Text and input styling */
.stTextInput, .stButton>button, input, textarea {
    background-color: rgba(0, 10, 0, 0.7) !important;
    color: #00FF41 !important;
    border-color: #00FF41 !important;
}

h1, h2, h3, p, div {
    color: #00FF41 !important;
}

/* Chat message styling */
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border: 1px solid #00FF41;
}

.chat-message.user {
    background-color: rgba(0, 50, 0, 0.4);
}

.chat-message.bot {
    background-color: rgba(0, 10, 0, 0.7);
}
</style>
""", unsafe_allow_html=True)

# App title
st.title("Matrix Gemini Chat")

# Debug information - this will help see what's happening
st.write("App is loading... If you see this, the basic UI is working.")

# Initialize chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat messages
st.write("Chat history:")
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    with st.container():
        st.markdown(f"<div class='chat-message {role}'>{content}</div>", unsafe_allow_html=True)

# Function to get response from Gemini
def get_gemini_response(prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"User query: {prompt}\n\nImportant: Your response must be strictly less than 100 words."
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Configure API key
try:
    # Try to get from secrets first
    try:
        api_key = st.secrets["gemini"]["api_key"]
        st.write("Found API key in secrets")
    except:
        # Fallback to manual entry for debugging
        api_key = st.text_input("Enter Gemini API Key for debugging:", type="password")
        if not api_key:
            st.warning("Please enter your API key")
            st.stop()
        st.write("Using manually entered API key")
    
    # Configure the API
    genai.configure(api_key=api_key)
    st.write("API configured successfully")
    
except Exception as e:
    st.error(f"Error configuring API: {str(e)}")
    st.stop()

# Simple user input
user_input = st.text_input("Your message:")

if st.button("Send") and user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get bot response
    with st.spinner("Thinking..."):
        bot_response = get_gemini_response(user_input)
    
    # Add bot response
    st.session_state.messages.append({"role": "bot", "content": bot_response})
    
    # Reload page to show new messages
    st.experimental_rerun()