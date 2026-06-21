import streamlit as st
import os
import tempfile
from PIL import Image
from google import genai

# --- Page Configuration ---
st.set_page_config(page_title="Enterprise Multimodal Chat", page_icon="🤖", layout="wide")
st.title("Multimodal AI Assistant")
st.markdown("Chat with the AI, upload documents for context, or share images for visual analysis.")

# --- Initialization ---
API_KEY = "AQ.Ab8RN6J8dnCzqS-JHmxAG15nFm2WtWB5MPlcLLVyUTMWNBwD6w"

# Cache the client so it doesn't reload on every UI interaction
@st.cache_resource
def get_client():
    return genai.Client(api_key=API_KEY)

client = get_client()

# Initialize the Gemini Chat Session in memory
if "chat_session" not in st.session_state:
    # Using gemini-2.5-flash as it is highly optimized for text, vision, and files
    st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")

# Initialize UI message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar for Uploads ---
with st.sidebar:
    st.header("📎 Attachments")
    st.markdown("Upload files before sending your message.")
    
    uploaded_file = st.file_uploader("Upload Document (PDF, TXT)", type=["pdf", "txt"])
    uploaded_image = st.file_uploader("Upload Image (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_session = client.chats.create(model="gemini-2.5-flash")
        st.rerun()

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input & Processing ---
if prompt := st.chat_input("Ask a question or describe what you want the AI to analyze..."):
    
    # 1. Display User Message in UI
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Prepare the payload for Gemini
    contents = [prompt]
    
    # 3. Handle Image Analysis
    if uploaded_image:
        image = Image.open(uploaded_image)
        contents.append(image)
        # Briefly show the image in the chat flow
        with st.chat_message("user"):
            st.image(image, caption="Attached Image", width=250)
            
    # 4. Handle Document/File Analysis
    if uploaded_file:
        # The Gemini Files API requires a physical file path to upload
        file_extension = uploaded_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name
            
        with st.spinner("Uploading document to AI securely..."):
            # Upload the file to Gemini's servers
            gemini_file = client.files.upload(file=temp_file_path)
            contents.append(gemini_file)
            
        # Clean up the temporary file from your local machine
        os.remove(temp_file_path) 
    
    # 5. Send Payload to AI and Get Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                # Send the combined text, image, and file data to the chat session
                response = st.session_state.chat_session.send_message(contents)
                
                # Display and save the response
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"An error occurred: {e}")