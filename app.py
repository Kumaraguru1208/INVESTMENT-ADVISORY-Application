import streamlit as st
from mychatbot import chatbot_response # Changed from mychatbot to chatbot as per your file name

st.set_page_config(page_title="Stock Price Prediction Chatbot", layout="centered")

st.markdown("<h1 style='text-align : center;'>TICKR-AI</h1>", unsafe_allow_html=True)
st.header("How can I Help You ?")
st.markdown("Hi! I am TICKR. I am here to help you with anything related to Stock Prediction.")

# --- Initialize Session State Variables ---
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial bot message
    st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I help you with stock predictions today?"})

# Initialize chatbot context for your chatbot.py logic
if "chatbot_context" not in st.session_state:
    st.session_state.chatbot_context = {"awaiting_ticker": False} # Matches initial context in your chatbot.py __main__

# --- Display Chat Messages ---
for message in st.session_state.messages:
    # Use "assistant" for bot messages for consistent styling and avatar
    role = "assistant" if message["role"] == "bot" else message["role"]
    with st.chat_message(role):
        st.markdown(message["content"])

# --- React to User Input ---
if prompt := st.chat_input("Ask about a stock..."):
    # 1. Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get bot response using your chatbot_response function
    #    Pass the user input AND the chatbot_context from session_state
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Pass the current context to your chatbot_response function
            response = chatbot_response(prompt, st.session_state.chatbot_context)
            st.markdown(response)

    # 3. Add bot response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})