import streamlit as st
import requests
import uuid
from datetime import datetime

# --- Configuration & Page Setup ---
st.set_page_config(
    page_title="The Regal Aurum Concierge",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://127.0.0.1:8000"
USER_AVATAR = "👤"
BOT_AVATAR = "✨"

# --- Client Session Token Validation ---
# Generates a persistent unique browser session token if not already present
if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

# --- Deep UI/UX Professional Theming (CSS Injection) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Global Canvas Reset */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header & Navigation Fixes */
    div[data-testid="stHeader"] {
        background-color: rgba(248, 250, 252, 0.8) !important;
        backdrop-filter: blur(8px);
        border-bottom: 1px solid #e2e8f0;
    }
    
    /* Layout Container Optimization */
    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom  : 6rem !important;
        max-width: 880px;
        margin: 0 auto;
    }
    
    /* Custom Sidebar Aesthetics */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding: 1.5rem !important;
    }
    
    /* Typography & Sidebar Headers */
    .sidebar-heading {
        font-weight: 700;
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 1.5rem 0 0.5rem 0;
    }
    
    /* New Chat Button Styling */
    .stButton > button[key^="new_chat_btn"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button[key^="new_chat_btn"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px 0 rgba(15, 23, 42, 0.15);
        background: linear-gradient(135deg, #334155 0%, #1e293b 100%) !important;
    }
    
    /* Chat History Navigation Links */
    div[data-testid="stSidebarUserContent"] .stButton > button {
        background-color: transparent !important;
        color: #334155 !important;
        border: 1px solid transparent !important;
        border-radius: 0.5rem !important;
        text-align: left !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease-in-out;
        display: block;
        width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    div[data-testid="stSidebarUserContent"] .stButton > button:hover {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border-color: #e2e8f0 !important;
    }
    
    /* Premium Message Component Overrides */
    .stChatMessage {
        padding: 1.25rem 1rem !important;
        border-radius: 0.75rem !important;
        margin-bottom: 1rem !important;
        transition: background-color 0.2s ease;
    }
    
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    }
    
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #f8fafc !important;
        border: 1px solid transparent !important;
    }
    
    /* Input Form Sticky Anchor Bar */
    .stChatInputContainer {
        border-radius: 0.75rem !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05) !important;
        padding: 0.25rem 0.5rem !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #64748b !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08) !important;
    }
/* Refined Feedback Button Array - NUCLEAR OVERRIDE */
    div[data-testid="column"] div[data-testid="stTooltipHoverTarget"],
    div[data-testid="column"] div[data-testid="stButton"],
    div[data-testid="column"] button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="column"] button[data-testid="baseButton-secondary"] {
        height: 38px !important;
        width: 38px !important;
        min-height: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 8px !important;
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }

    div[data-testid="column"] button[data-testid="baseButton-secondary"]:hover {
        background-color: #e2e8f0 !important;
        transform: translateY(-1px);
    }

    div[data-testid="column"] button[data-testid="baseButton-secondary"] p {
        font-size: 1.25rem !important;
        margin: 0 !important;
        line-height: 1 !important;
    }
    /* Branding Elements */
    .brand-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
        text-align: center;
    }
    
    .brand-subtitle {
        font-size: 0.875rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2.5rem;
    }
    </style>
""", unsafe_allow_html=True)


# --- Core Logic Functions & Context Managers ---

def fetch_chat_history(session_id: str):
    """Retrieves conversation historical logs from the backend microservice data layers."""
    try:
        response = requests.get(f"{API_BASE_URL}/sessions/{session_id}/history")
        if response.status_code == 200:
            st.session_state.messages = response.json()
        else:
            st.session_state.messages = []
            st.error("Failed to sync structural conversation logs.")
    except Exception as e:
        st.session_state.messages = []
        st.error(f"Network transport fault: {str(e)}")


def initialize_new_session():
    """Requests a cleanly mapped, non-colliding runtime session ID tied to browser token context."""
    try:
        payload = {"client_id": st.session_state.client_id}
        response = requests.post(f"{API_BASE_URL}/sessions", json=payload)
        if response.status_code == 200:
            st.session_state.session_id = response.json().get("session_id")
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Welcome to **The Regal Aurum**. How may I assist you with your luxury stay, reservations, or dynamic hotel amenities today?"
                }
            ]
        else:
            st.error("Authentication backend context failed to provision identifier.")
    except Exception as e:
        st.error(f"Upstream pipeline connection failure: {str(e)}")


def transmit_user_feedback(message_id: str, feedback_rating: str):
    """Submits transactional telemetry event metadata (likes/dislikes) straight to Neon DB."""
    try:
        payload = {"feedback": feedback_rating}
        url = f"{API_BASE_URL}/messages/{message_id}/feedback"
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.toast(f"Feedback recorded: Confirmed {feedback_rating.upper()}", icon="✅")
        else:
            st.toast("Feedback processing encountered an infrastructure layer error.", icon="⚠️")
    except Exception as e:
        st.toast(f"Feedback telemetry transmission failure: {str(e)}", icon="❌")


# --- Verification Guard ---
if "session_id" not in st.session_state:
    initialize_new_session()


# --- Sidebar Component Shell (Scoped Single-Tenant Architecture) ---
with st.sidebar:
    st.markdown("<div style='padding: 0.5rem 0;'><h2 style='font-size: 1.25rem; font-weight:700; color:#0f172a; margin:0;'>Dashboard Context</h2></div>", unsafe_allow_html=True)
    
    # Structural Action Triggers
    if st.button("➕ New Interaction Thread", key="new_chat_btn", use_container_width=True):
        initialize_new_session()
        st.rerun()
        
    st.markdown("<div class='sidebar-heading'>Isolated Storage Logs</div>", unsafe_allow_html=True)
    
    # Query database records bounded tightly to this specific local user instance client token
    try:
        query_params = {"client_id": st.session_state.client_id}
        history_response = requests.get(f"{API_BASE_URL}/sessions", params=query_params)
        
        if history_response.status_code == 200:
            all_sessions = history_response.json()
            if not all_sessions:
                st.markdown("<div style='font-size:0.85rem; color:#94a3b8; padding-left:0.5rem;'>No past history threads located.</div>", unsafe_allow_html=True)
            else:
                for session_item in all_sessions:
                    is_active = session_item['id'] == st.session_state.session_id
                    btn_prefix = "📌 " if is_active else "💬 "
                    
                    if st.button(
                        f"{btn_prefix}{session_item['title']}", 
                        key=f"sid_{session_item['id']}", 
                        use_container_width=True
                    ):
                        fetch_chat_history(session_item['id'])
                        st.session_state.session_id = session_item['id']
                        st.rerun()
        else:
            st.markdown("<div style='font-size:0.85rem; color:#ef4444;'>Failed to extract sidebar timeline logs.</div>", unsafe_allow_html=True)
    except Exception:
        st.markdown("<div style='font-size:0.85rem; color:#ef4444;'>Security context tracking structural offline.</div>", unsafe_allow_html=True)

# --- Core View Workspace Generation ---
st.markdown("<div class='brand-title'>The Regal Aurum</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>Generative Intelligence Concierge System v1.2</div>", unsafe_allow_html=True)

# Render Structural Context Conversation Streams Natively
for index, msg_node in enumerate(st.session_state.messages):
    with st.chat_message(msg_node["role"], avatar=USER_AVATAR if msg_node["role"] == "user" else BOT_AVATAR):
        st.markdown(msg_node["content"])
        
        # Interactive Metadata Controls Render Layer (Bot Interfacing Columns)
        if msg_node["role"] == "assistant" and "id" in msg_node:
            # FIXED: Smaller, highly precise column ratios to prevent wrapping or misaligned blocks
            fb_col1, fb_col2, fb_col3, _ = st.columns([1, 1, 1, 12])
            
            with fb_col1:
                st.markdown('<div class="feedback-col">', unsafe_allow_html=True)
                if st.button("👍", key=f"lk_{msg_node['id']}_{index}", help="Upvote response"):
                    transmit_user_feedback(msg_node['id'], "like")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with fb_col2:
                st.markdown('<div class="feedback-col">', unsafe_allow_html=True)
                if st.button("👎", key=f"dlk_{msg_node['id']}_{index}", help="Downvote response"):
                    transmit_user_feedback(msg_node['id'], "dislike")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with fb_col3:
                st.markdown('<div class="feedback-col">', unsafe_allow_html=True)
                if st.button("📋", key=f"cp_{msg_node['id']}_{index}", help="Copy text"):
                    st.toast("Text section ready! Drag or highlight to copy content.", icon="ℹ️")
                st.markdown('</div>', unsafe_allow_html=True)


# --- Input Engine Event Handler Processing Loop ---
if raw_input_string := st.chat_input("Ask about hotel services, premium dining bookings, policy metrics..."):
    # Secure immediate representation to screen canvas state structures
    st.session_state.messages.append({"role": "user", "content": raw_input_string})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(raw_input_string)
        
    # Open processing generation visualization thread
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Processing system intent routes and matching document structures..."):
            try:
                request_payload = {
                    "session_id": st.session_state.session_id, 
                    "query": raw_input_string
                }
                api_response = requests.post(f"{API_BASE_URL}/chat", json=request_payload)
                
                if api_response.status_code == 200:
                    json_data_payload = api_response.json()
                    extracted_text = json_data_payload.get('response')
                    generated_msg_uuid = json_data_payload.get('message_id')
                    
                    # Output explicitly to frontend UI layout view
                    st.markdown(extracted_text)
                    
                    # Store explicitly within structural instance arrays
                    st.session_state.messages.append({
                        "id": generated_msg_uuid, 
                        "role": "assistant", 
                        "content": extracted_text
                    })
                    st.rerun()
                else:
                    st.error(f"Backend Engine returned an operational fault status: {api_response.status_code}")
            except Exception as system_exception:
                st.error(f"Critical execution error during network transaction: {str(system_exception)}")