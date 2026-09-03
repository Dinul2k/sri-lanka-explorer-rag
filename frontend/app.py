import streamlit as st
import requests
import os
import time

# Minimalistic config
st.set_page_config(page_title="Sri Lanka Tourism Guide", page_icon="🌴", layout="centered")

# Custom CSS for modern/minimalist look
st.markdown("""
<style>
    /* Hide the Streamlit header and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Clean up the main container */
    .main {
        padding-top: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* Metadata styling */
    .metadata-text {
        font-size: 0.8rem;
        color: #888;
        margin-top: 5px;
    }
    .badge {
        display: inline-block;
        padding: 0.25em 0.4em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
        background-color: #6c757d;
        color: white;
    }
    .badge-cache { background-color: #28a745; }
    .badge-rag { background-color: #007bff; }
</style>
""", unsafe_allow_html=True)

st.title("🌴 Sri Lanka Explorer")
st.markdown("Ask anything about your trip to Sri Lanka!")

API_URL = os.environ.get("API_URL", "http://localhost:8001/query")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message:
            st.markdown(message["metadata"], unsafe_allow_html=True)

# React to user input
if prompt := st.chat_input("Where would you like to go? (e.g. Best beaches in Galle)"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                start_time = time.time()
                response = requests.post(API_URL, json={"query": prompt}, timeout=600)
                response.raise_for_status()
                data = response.json()
                latency = time.time() - start_time
                
                answer = data.get("response", "Sorry, I couldn't understand the response.")
                source = data.get("source", "unknown")
                
                message_placeholder.markdown(answer)
                
                # Format metadata
                badge_class = "badge-cache" if source == "cache" else "badge-rag"
                metadata_html = f"""
                <div class='metadata-text'>
                    Source: <span class='badge {badge_class}'>{source}</span> | 
                    Latency: {latency:.2f}s
                </div>
                """
                st.markdown(metadata_html, unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "metadata": metadata_html
                })
                
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the backend. It might still be starting up (e.g. downloading AI models). Please wait a few minutes and try again.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with the backend: {e}")
