import streamlit as st

st.markdown("<h1 style='text-align : center;'>TICKR-AI</h1>",unsafe_allow_html=True)
st.header("How can I Help You ?")
data=st.text_input("",placeholder="start to type !")
st.markdown("Hi! I am TICKR . I am here to help you with anything related to Stock Prediction")
if st.button("SUBMIT"):
    st.write(f"HI {data}")
