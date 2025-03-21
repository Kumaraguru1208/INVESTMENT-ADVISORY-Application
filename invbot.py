import yfinance as yf
import ta

def get_stock_data(ticker, period='6mo', interval='1d'):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)

    if df.empty or len(df) < 50:
        print(f"⚠️ Insufficient data for {ticker}")  # Debugging output
        return None  # Handle insufficient data case

    return df

def moving_average_strategy(ticker, short_window=20, long_window=50):
    df = get_stock_data(ticker)
    if df is None:
        return f"Data unavailable for {ticker}. Please check the ticker symbol."

    df['Short_MA'] = df['Close'].rolling(window=short_window).mean()
    df['Long_MA'] = df['Close'].rolling(window=long_window).mean()

    # Debugging print statements
    print(f"\n📊 Debugging {ticker} Moving Averages:")
    print(f"Short_MA Last Value: {df['Short_MA'].iloc[-1]}")
    print(f"Long_MA Last Value: {df['Long_MA'].iloc[-1]}")

    if df['Short_MA'].iloc[-1] > df['Long_MA'].iloc[-1]:
        return f"BUY {ticker} (Short MA: {df['Short_MA'].iloc[-1]:.2f} > Long MA: {df['Long_MA'].iloc[-1]:.2f})"
    elif df['Short_MA'].iloc[-1] < df['Long_MA'].iloc[-1]:
        return f"SELL {ticker} (Short MA: {df['Short_MA'].iloc[-1]:.2f} < Long MA: {df['Long_MA'].iloc[-1]:.2f})"
    else:
        return f"HOLD {ticker} (Short MA and Long MA are nearly equal)"

def rsi_strategy(ticker):
    df = get_stock_data(ticker)
    if df is None:
        return f"Data unavailable for {ticker}. Please check the ticker symbol."

    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=10).rsi()

    # Debugging print statements
    print(f"\n📊 Debugging {ticker} RSI:")
    print(f"RSI Last Value: {df['RSI'].iloc[-1]:.2f}")

    if df['RSI'].iloc[-1] < 30:
        return f"BUY {ticker} (RSI: {df['RSI'].iloc[-1]:.2f}, Oversold)"
    elif df['RSI'].iloc[-1] > 70:
        return f"SELL {ticker} (RSI: {df['RSI'].iloc[-1]:.2f}, Overbought)"
    else:
        return f"HOLD {ticker} (RSI: {df['RSI'].iloc[-1]:.2f}, Neutral)"

def analyze_stock(ticker):
    ticker = ticker.upper()
    ma_result = moving_average_strategy(ticker)
    rsi_result = rsi_strategy(ticker)
    return f"{ma_result}\n\t{rsi_result}"
