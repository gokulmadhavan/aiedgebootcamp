# Prompts used for this project

## Prompts to Claude

### Initial prompt
ROLE: You are an experienced coder and AI software developer.
CONTEXT: I am a beginner at AI programming. I have never used LangChain before.
TASK:
I want to create a LangChain-based chatbot in Python which I will host on Streamlit Community Cloud. The app should obey the following constraints:
* It should be context-aware for the session.
* It should ask for a Gemini API Key to start the chat.
* It should use Gemini API to allow the chat.
* It should have an "End" button.  When the "End" button is pressed, it should make a LangChain-based API call to OpenAI to (1) summarize the chat in under 150 words, and (2) perform a sentiment analysis of the conversation.
Provide me with instructions for setting up LangChain and the app and for storing API keys securely.