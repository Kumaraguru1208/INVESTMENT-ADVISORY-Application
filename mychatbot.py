import random
import re
import time
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import warnings
import requests
import json # Import json for JSONDecodeError

warnings.filterwarnings("ignore")

# === Responses ===
responses = {
    "hello": ["Hello", "Hi", "Hey! How can I help you?"],
    "hi": ["Hello", "Hi", "Hey! How can I help you?"],
    "how are you": ["I am fine", "I am fine, how are you?"],
    "i am fine": ["How can I help you?", "Good! How can I help you?"],
    "can you analyze the stock price": [
        "Sure! Please tell me the name of the company or stock ticker you want to analyze."
    ],
    "stock prediction": [
        "Provide the company name or stock ticker for which you need the stock prediction."
    ]
}

# --- API Keys ---
ALPHA_VANTAGE_API_KEY = 'QNIAZCDQ7DFS1NU4' # Replace with your actual key
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# --- Currency Conversion ---
def get_usd_to_inr_exchange_rate():
    """
    Fetches the current USD to INR exchange rate using Alpha Vantage.
    Returns the exchange rate as a float, or None if fetching fails.
    """
    function = "CURRENCY_EXCHANGE_RATE"
    from_currency = "USD"
    to_currency = "INR"
    params = {
        "function": function,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    print(f"Attempting to fetch USD to INR exchange rate from Alpha Vantage...")
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "Realtime Currency Exchange Rate" in data:
            exchange_rate = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            print(f"Successfully fetched USD to INR rate: {exchange_rate:.2f}")
            return exchange_rate
        else:
            print(f"Alpha Vantage: Could not get USD to INR exchange rate. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch USD to INR rate (network/API error): {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON for USD to INR rate: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching USD to INR rate: {e}")
        return None


# --- Data Fetching Functions ---
def fetch_data_alpha_vantage(ticker):
    """
    Attempts to fetch daily stock data from Alpha Vantage.
    Returns DataFrame if successful, None otherwise.
    NOTE: For Indian stocks with Alpha Vantage, use format like 'NSE:RELIANCE' or 'BSE:500325'.
    """
    function = "TIME_SERIES_DAILY"
    params = {
        "function": function,
        "symbol": ticker,
        "outputsize": "compact", # 'compact' for last 100 days, 'full' for 20+ years
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    print(f"Attempting to fetch data for {ticker.upper()} from Alpha Vantage...")
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if "Error Message" in data:
            print(f"Alpha Vantage Error: {data['Error Message']}")
            return None
        if "Time Series (Daily)" not in data:
            print(f"Alpha Vantage: 'Time Series (Daily)' not found for {ticker.upper()}. Data might be incomplete or ticker not found.")
            return None

        df = pd.DataFrame(data["Time Series (Daily)"]).T
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        df = df.sort_index() # Ensure oldest to latest
        print(f"Successfully fetched data from Alpha Vantage for {ticker.upper()}.")
        return df

    except requests.exceptions.RequestException as e:
        print(f"Alpha Vantage API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from Alpha Vantage response: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred with Alpha Vantage: {e}")
        return None

def fetch_data_yfinance(ticker):
    """
    Attempts to fetch daily stock data from yfinance.
    Returns DataFrame if successful, None otherwise.
    NOTE: For Indian stocks with yfinance, use suffix '.NS' (NSE) or '.BO' (BSE).
    e.g., 'RELIANCE.NS'
    """
    print(f"Attempting to fetch data for {ticker.upper()} from yfinance...")
    try:
        ticker_data = yf.Ticker(ticker)
        # Fetch historical data for the last 1 year (adjust 'period' as needed)
        df = ticker_data.history(period="1y", interval="1d")
        
        if df.empty:
            print(f"yfinance: No historical data found for {ticker.upper()}.")
            return None
        
        # Rename columns to match Alpha Vantage for consistency in prediction logic
        df.rename(columns={
            "Open": "1. open",
            "High": "2. high",
            "Low": "3. low",
            "Close": "4. close",
            "Volume": "5. volume"
        }, inplace=True)
        
        # Drop any columns not needed for prediction to maintain consistency
        df = df[["1. open", "2. high", "3. low", "4. close", "5. volume"]]
        
        df.index = pd.to_datetime(df.index.date) # Convert timezone-aware index to date-only
        df = df.sort_index() # Ensure oldest to latest
        
        print(f"Successfully fetched data from yfinance for {ticker.upper()}.")
        return df
    except Exception as e:
        print(f"yfinance data fetch failed for {ticker.upper()}: {e}")
        return None

# --- Main Prediction Function with Failover and Currency Conversion ---
def get_stock_predictions(ticker):
    """
    Fetches stock data with yfinance as primary and Alpha Vantage as failover,
    performs linear regression for prediction, and converts prices to INR.
    """
    # Ensure ticker is uppercase for consistent use
    ticker = ticker.upper() 

    # --- Step 1: Get USD to INR exchange rate ---
    usd_to_inr_rate = get_usd_to_inr_exchange_rate()
    if usd_to_inr_rate is None:
        print("Warning: Could not get USD to INR exchange rate. Prices will be displayed in USD.")
        usd_to_inr_rate = 1.0 # Default to 1.0 to avoid multiplication errors, effectively showing USD

    # --- Step 2: Try yfinance (Primary) ---
    # Determine the yfinance ticker format for Indian stocks
    # Assuming user might input 'RELIANCE' and we need to try '.NS' and '.BO'
    # Or, if they provide 'RELIANCE.NS', we use that directly.
    yfinance_ticker = ticker
    if not (yfinance_ticker.endswith(".NS") or yfinance_ticker.endswith(".BO")):
        # If no suffix, try common NSE suffix first
        yfinance_ticker_nse = ticker + ".NS"
        df = fetch_data_yfinance(yfinance_ticker_nse)
        if df is None or df.empty:
            # If NSE suffix fails, try BSE suffix
            yfinance_ticker_bse = ticker + ".BO"
            df = fetch_data_yfinance(yfinance_ticker_bse)
    else:
        # If user provided a suffix, use it directly
        df = fetch_data_yfinance(yfinance_ticker)

    # --- Step 3: If yfinance failed, try Alpha Vantage (Failover) ---
    if df is None or df.empty:
        print(f"yfinance failed for {ticker}. Attempting Alpha Vantage fallback...")
        time.sleep(1) # Small delay before trying failover to be gentle on APIs
        
        # Determine the Alpha Vantage ticker format for Indian stocks
        # Assuming user might input 'RELIANCE' and we need to try 'NSE:RELIANCE'
        alpha_vantage_ticker = ticker
        if not alpha_vantage_ticker.startswith("NSE:") and not alpha_vantage_ticker.startswith("BSE:"):
             # If no prefix, assume NSE as default for Alpha Vantage failover
             alpha_vantage_ticker = "NSE:" + ticker
        
        df = fetch_data_alpha_vantage(alpha_vantage_ticker)

    # --- Step 4: If data is still not available after failover ---
    if df is None or df.empty:
        return f"⚠️ Couldn't fetch data for {ticker} from both yfinance and Alpha Vantage. Please check the ticker or try again later."

    # --- Step 5: Convert prices to INR if exchange rate is available ---
    if usd_to_inr_rate != 1.0: # Only convert if we actually got a rate
        print(f"Converting stock prices to INR using rate: {usd_to_inr_rate:.2f}")
        for col in ["1. open", "2. high", "3. low", "4. close"]:
            df[col] = df[col] * usd_to_inr_rate

    # --- Step 6: Proceed with prediction ---
    try:
        df["Days"] = np.arange(len(df)).reshape(-1, 1)

        model = LinearRegression()
        model.fit(df[["Days"]], df["4. close"])

        next_day = np.array([[len(df)]])
        prediction = model.predict(next_day)

        latest_price = df["4. close"].iloc[-1]

        currency_symbol = "₹" if usd_to_inr_rate != 1.0 else "$"

        if prediction[0] > latest_price:
            advice = "📈 Suggested Action: BUY — the price is expected to rise."
        elif prediction[0] < latest_price:
            advice = "📉 Suggested Action: SELL — the price is expected to drop."
        else:
            advice = "🔍 Suggested Action: HOLD — the price is expected to remain stable."

        return (f"📊 Stock Analysis for {ticker}\n"
                f"The latest closing price of {ticker} is {currency_symbol}{latest_price:.2f}.\n"
                f"The predicted price for the next trading day is {currency_symbol}{prediction[0]:.2f}.\n"
                f"{advice}")

    except Exception as e:
        return f"❌ An error occurred during prediction for {ticker}: {str(e)}. Data might be insufficient."

# === Context-Aware Chatbot ===
def chatbot_response(user_input , context ):
    user_input_clean = user_input.lower().strip()

    # Check if waiting for a ticker
    if context.get("awaiting_ticker"):
        context["awaiting_ticker"] = False
        return get_stock_predictions(user_input.upper())

    # Direct keyword check for intent
    if any(word in user_input_clean for word in ["stock", "analyze", "price", "prediction"]):
        match = re.search(r"(?:of|for|about)\s+([A-Za-z.\-]+)", user_input_clean)
        if match:
            company = match.group(1).strip().upper()
            return get_stock_predictions(company)
        else:
            context["awaiting_ticker"] = True
            return "Sure! Please provide the company name or stock ticker to analyze."

    # Exact match for FAQs
    if user_input_clean in responses:
        return random.choice(responses[user_input_clean])

    # If the user types a possible ticker and context is not set
    if re.match(r"^[A-Za-z.\-]{1,5}$", user_input_clean.upper()):
        return "Can you clarify what you'd like me to do with this ticker? Try saying 'analyze the stock of AAPL'."

    return "I'm sorry, I didn't understand that. Can you rephrase?"

# === Main loop ===
if __name__ == "__main__":
    print("Welcome to StockBot! Type 'exit' to leave.")
    context = {"awaiting_ticker": False}

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye! Have a nice day! 😊")
            break
        response = chatbot_response(user_input, context)
        print("Chatbot:", response)