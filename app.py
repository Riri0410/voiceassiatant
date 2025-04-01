import streamlit as st
import os
import tempfile
from google import genai
from google.genai import types
#from dotenv import load_dotenv
import pandas as pd
from audio_recorder_streamlit import audio_recorder
# import toml

# Load environment variables
#load_dotenv()

# Initialize user data
users_data = {
    "001": {"user_id": "001", "name": "John Doe", "email": "john.doe@example.com", "balance": 100.0},
    "002": {"user_id": "002", "name": "Jane Smith", "email": "jane.smith@example.com", "balance": 200.0},
    "003": {"user_id": "003", "name": "Michael Brown", "email": "michael.brown@example.com", "balance": 150.0},
}

# Page configuration
st.set_page_config(
    page_title="Voice Assistant",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Voice Chat"

# Initialize Gemini client
client = None  # Initialize as None first
try:
    GOOGLE_API_KEY=toml.load(".streamlit/config.toml")
    client = genai.Client(api_key="AIzaSyAXoYTl5VEPt_ATdpIclI7zzXrIzDBolig")
except KeyError:
    st.error("Google API key not found in Streamlit secrets. Please add it to your secrets.toml file.")
except Exception as e:
    st.error(f"Failed to initialize Gemini client: {str(e)}")


def save_audio_file(audio_bytes):
    """Save audio bytes to a temporary file and return the path"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_file.write(audio_bytes)
    temp_file.close()
    return temp_file.name


def process_audio(audio_path):
    try:
        # Upload the file
        uploaded_file = client.files.upload(file=audio_path)

        # Create content with prompt - CORRECTED VERSION
        contents = types.Content(
            role="user",
            parts=[
                types.Part.from_uri(file_uri=uploaded_file.uri, mime_type="audio/wav"),
                types.Part.from_text(text="""You are a helpful voice assistant. Keep responses concise and friendly."""),
            ],
        )

        # Get response from Gemini - CORRECTED MODEL NAME (fixed typo)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",  # Updated to current model name
            contents=[contents]
        )
        return response.text

    except Exception as e:
        return f"Sorry, I couldn't process your audio. Error: {str(e)}"


def send_audio_message(audio_file):
    """Process the audio and send the message"""
    st.session_state.processing = True
    if audio_file:
        response = process_audio(audio_file)
        st.session_state.messages.append({"role": "user", "content": "🗣️ Voice message sent"})
        st.session_state.messages.append({"role": "assistant", "content": response})
        os.unlink(audio_file)
        st.session_state.processing = False
    st.rerun()


# UI Structure
st.sidebar.title("Navigation")
tabs = ["Voice Chat", "User Data"]
st.session_state.current_tab = st.sidebar.radio("Go to", tabs)

if st.session_state.current_tab == "Voice Chat":
    st.title("🎤 Voice Assistant")
    chat_container = st.container(height=400)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    if st.session_state.processing:
        with st.spinner("Processing your message..."):
            pass
    else:
        # Audio recorder widget
        audio_data = audio_recorder(pause_threshold=2.0, sample_rate=16000)

        if audio_data:
            st.audio(audio_data, format="audio/wav")

            # Save the audio to a temporary file
            temp_audio_file = save_audio_file(audio_data)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Send Message", use_container_width=True, type="primary"):
                    send_audio_message(temp_audio_file)
            with col2:
                if st.button("Cancel", use_container_width=True):
                    os.unlink(temp_audio_file)
                    st.rerun()

    if st.session_state.messages and st.button("Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.rerun()

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.write("👋 Hello! I'm your voice assistant. Click the record button to talk to me.")

elif st.session_state.current_tab == "User Data":
    st.title("📊 User Data")
    users_df = pd.DataFrame.from_dict(users_data, orient='index')
    st.dataframe(users_df, use_container_width=True)
    with st.expander("View Raw JSON"):
        st.json(users_data)
