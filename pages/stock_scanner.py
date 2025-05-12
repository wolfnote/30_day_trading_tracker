
import streamlit as st
import pandas as pd
import requests
import time

# -------------------------------------
# 🔐 Load API Key from secrets
# -------------------------------------
API_KEY = st.secrets["finnhub_api_key"]

# -------------------------------------
# 🔎 Predefined Tickers List (Top Volume/Momentum Symbols)
# Replace with dynamic source later if needed
# -------------------------------------
SYMBOLS = [
    "TSLA", "NVDA", "AMD", "AAPL", "BAOS", "FRGT", "YHC", "MARA", "RIOT", "PLTR",
    "SPY", "GME", "AMC", "BBAI", "CVNA", "TQQQ", "SOUN", "FFIE", "NKLA", "GOEV"
]

# -------------------------------------
# 📥 Fetch Finnhub Quote & Profile Data
# -------------------------------------
def fetch_stock_data(symbol):
    try:
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={API_KEY}"

        quote = requests.get(quote_url).json()
        profile = requests.get(profile_url).json()

        current_price = quote.get("c")
        previous_close = quote.get("pc")
        percent_change = round(((current_price - previous_close) / previous_close) * 100, 2) if previous_close else 0

        return {
            "Symbol": symbol,
            "Price": current_price,
            "% Change": percent_change,
            "Volume": quote.get("v"),
            "Market Cap": profile.get("marketCapitalization", 0),
            "Float": profile.get("shareOutstanding", 0)
        }

    except Exception as e:
        return {"Symbol": symbol, "Error": str(e)}

# -------------------------------------
# 🧠 Filtering Logic
# -------------------------------------
def meets_criteria(stock):
    try:
        return (
            stock["Price"] is not None and 1 <= stock["Price"] <= 20 and
            stock["% Change"] > 10 and
            stock.get("Volume", 0) >= 1_000_000 and
            stock.get("Float", 9999) <= 20 and
            stock.get("Market Cap", 9999) <= 500
        )
    except:
        return False

# -------------------------------------
# 📊 Streamlit UI
# -------------------------------------
st.set_page_config(page_title="🧠 Auto Stock Scanner", layout="wide")
st.title("🧠 Auto-Filtered Stock Scanner (Free Tier Friendly)")

st.info("Scanning selected symbols with real-time quote and profile filters...")

results = []
count = 0

for symbol in SYMBOLS:
    stock = fetch_stock_data(symbol)
    if meets_criteria(stock):
        results.append(stock)

    # Respect Finnhub's free tier limit (60 requests/min = 1 request/sec)
    count += 2
    if count >= 58:
        st.warning("⏳ API limit hit, stopping scan early.")
        break
    time.sleep(1)  # 1 sec delay between API hits

if results:
    df = pd.DataFrame(results)
    st.success(f"✅ Found {len(df)} stocks matching your criteria.")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("🚫 No stocks matched the filter at this time.")
