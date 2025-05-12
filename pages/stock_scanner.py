
import streamlit as st
import pandas as pd
import requests

# -------------------------------
# 🧾 CONFIG
# -------------------------------
API_KEY = "YOUR_FINNHUB_API_KEY"  # Replace with your actual API key
SYMBOLS = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "AMZN", "GOOGL", "BAOS", "YHC", "FRGT"]

# -------------------------------
# 🔧 Fetch Quote Data
# -------------------------------
def fetch_quote(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "Symbol": symbol,
            "Price": data.get("c"),
            "% Change": round(((data.get("c") - data.get("pc")) / data.get("pc")) * 100, 2) if data.get("pc") else None,
            "High": data.get("h"),
            "Low": data.get("l"),
            "Open": data.get("o"),
            "Previous Close": data.get("pc")
        }
    else:
        return {"Symbol": symbol, "Error": f"Failed to fetch data ({response.status_code})"}

# -------------------------------
# 📊 Main App
# -------------------------------
st.set_page_config(page_title="Real-Time Stock Scanner", layout="wide")
st.title("🔍 Real-Time Stock Scanner (Powered by Finnhub.io)")

selected_symbols = st.multiselect("Select Stocks to Scan", options=SYMBOLS, default=SYMBOLS[:5])

if st.button("🔄 Refresh Data"):
    st.info("Fetching data...")
    all_data = [fetch_quote(symbol) for symbol in selected_symbols]
    df = pd.DataFrame(all_data)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("👆 Click 'Refresh Data' to load stock information.")
