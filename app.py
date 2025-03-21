import streamlit as st
import yfinance as yf

st.title("Stock Price Prediction Bot 📈")

# Get stock input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA)", "AAPL")

if st.button("Get Stock Data"):
    stock = yf.Ticker(ticker)
    data = stock.history(period="6mo")
    st.line_chart(data['Close'])