import os
import tempfile
import streamlit as st
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# Set page configuration
st.set_page_config(page_title="Document Q&A Bot", layout="wide")
st.title("Document Q&A Bot")

# Initialize session state variables
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_processed" not in st.session_state:
    st.session_state.document_processed = False

# OpenAI API Key input
api_key = st.sidebar.text_input("Enter your OpenAI API Key:", type="password")
os.environ["OPENAI_API_KEY"] = api_key

# Function to process uploaded document
def process_document(uploaded_file):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    # Load document based on file type
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        loader = PyPDFLoader(tmp_path)
    elif file_extension == 'txt':
        loader = TextLoader(tmp_path)
    elif file_extension in ['docx', 'doc']:
        loader = Docx2txtLoader(tmp_path)
    else:
        st.error(f"Unsupported file format: {file_extension}")
        os.unlink(tmp_path)  # Clean up temp file
        return None
    
    documents = loader.load()
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Clean up temp file
    os.unlink(tmp_path)
    
    return vectorstore

# Custom prompt template
qa_template = """
You are a helpful AI assistant that answers questions based ONLY on the provided document.
If the question cannot be answered using the document information, politely decline to answer and explain that you can only provide information from the uploaded document.

Context: {context}

Chat History: {chat_history}

Question: {question}

Answer:
"""

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload a document (PDF, TXT, DOCX)", type=["pdf", "txt", "docx"])

if uploaded_file and api_key:
    with st.spinner("Processing document..."):
        # Process the document and create the conversational chain
        vectorstore = process_document(uploaded_file)
        
        if vectorstore:
            # Create memory and retrieval chain
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            
            # Create prompt
            PROMPT = PromptTemplate(
                template=qa_template,
                input_variables=["context", "chat_history", "question"]
            )
            
            # Create chain
            llm = ChatOpenAI(temperature=0, model="gpt-4o")
            st.session_state.conversation = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
                memory=memory,
                combine_docs_chain_kwargs={"prompt": PROMPT}
            )
            st.session_state.document_processed = True
            st.sidebar.success(f"Document '{uploaded_file.name}' processed successfully!")

# Chat interface
if st.session_state.document_processed:
    st.subheader("Ask questions about your document")
    
    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:  # User message
            with st.chat_message("user"):
                st.write(message.content)
        else:  # AI message
            with st.chat_message("assistant"):
                st.write(message.content)
    
    # User input
    user_question = st.chat_input("Ask a question about your document")
    
    if user_question:
        with st.chat_message("user"):
            st.write(user_question)
        
        with st.spinner("Thinking..."):
            from langchain.schema import HumanMessage, AIMessage
            
            # Get conversation response
            response = st.session_state.conversation.invoke({"question": user_question})
            ai_response = response["answer"]
            
            # Update chat history
            st.session_state.chat_history.append(HumanMessage(content=user_question))
            st.session_state.chat_history.append(AIMessage(content=ai_response))
        
        # Display AI response
        with st.chat_message("assistant"):
            st.write(ai_response)
else:
    if not api_key:
        st.info("Please enter your OpenAI API key in the sidebar.")
    else:
        st.info("Please upload a document to begin.")

# Add some instructions in the sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("How to use:")
st.sidebar.markdown("""
1. Enter your OpenAI API key
2. Upload a document (PDF, TXT, or DOCX)
3. Ask questions about the content of your document
4. The assistant will only answer questions based on the document content
""")