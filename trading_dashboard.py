# trading_dashboard_app.py

import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
from io import StringIO

# -------------------------------
# 🌟 USER SETTINGS
# -------------------------------
USERNAME = "wolfnote"
PASSWORD = "Beograd!98o"

st.set_page_config(page_title="Trading Dashboard", layout="wide")

# -------------------------------
# 🔌 Unified Query Function
# -------------------------------
def run_query(query, params=None):
    with psycopg2.connect(
        host=st.secrets["host"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        dbname=st.secrets["database"],
        sslmode='require'
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:
                return cursor.fetchall()
            conn.commit()

# -------------------------------
# 🌓 Theme
# -------------------------------
def set_theme():
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
    st.session_state["dark_mode"] = st.sidebar.checkbox("🌓 Dark Mode", value=st.session_state["dark_mode"])
    st.markdown(
        f"""
        <style>
        .reportview-container {{
            background-color: {'#0e1117' if st.session_state["dark_mode"] else 'white'};
            color: {'white' if st.session_state["dark_mode"] else 'black'};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# -------------------------------
# 🔐 Login
# -------------------------------
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state["authenticated"] = True
        else:
            st.sidebar.error("Invalid credentials")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# -------------------------------
# 🌙 Theme
# -------------------------------
set_theme()

# -------------------------------
# 📋 Trade Entry Form
# -------------------------------
st.title("📈 Trading Dashboard")

with st.form("trade_form"):
    st.subheader("➕ Add New Trade")
    date = st.date_input("Date")
    strategy = st.selectbox("Strategy", ["Gap & Go", "Momentum", "Dip Buy", "Reversal", "Other"])
    symbol = st.text_input("Stock Symbol").upper()
    entry = st.number_input("Entry Price", format="%.2f")
    exit = st.number_input("Exit Price", format="%.2f")
    shares = st.number_input("Shares", min_value=1, step=1)
    fees = st.number_input("Fees", value=0.0, format="%.2f")
    paper = st.checkbox("Paper Trading")
    ondemand = st.checkbox("OnDemand Trade")

    submitted = st.form_submit_button("💾 Save Trade")
    if submitted:
        gain_loss = (exit - entry) * shares - fees
        total_investment = entry * shares
        return_pct = (gain_loss / total_investment) * 100 if total_investment else 0
        run_query(
            """INSERT INTO trades (date, strategy, symbol, entry, exit, shares, fees, gain_loss, return_pct, total_investment, paper_trade, ondemand_trade)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (date.strftime("%m-%d-%Y"), strategy, symbol, entry, exit, shares, fees, gain_loss, return_pct, total_investment, paper, ondemand)
        )
        st.success("Trade saved!")

# -------------------------------
# 🔍 Filters
# -------------------------------
st.sidebar.header("📊 Filters")
strategy_filter = st.sidebar.multiselect("Filter by Strategy", ["Gap & Go", "Momentum", "Dip Buy", "Reversal", "Other"])
paper_only = st.sidebar.checkbox("Show Only Paper Trades")
ondemand_only = st.sidebar.checkbox("Show Only OnDemand Trades")

# -------------------------------
# 📤 Export & Display
# -------------------------------
query = "SELECT id, date, strategy, symbol, entry, exit, shares, fees, gain_loss, return_pct, total_investment, paper_trade, ondemand_trade FROM trades"
data = pd.DataFrame(run_query(query), columns=[
    "ID", "Date", "Strategy", "Symbol", "Entry", "Exit", "Shares", "Fees", "Gain/Loss", "Return %", "Total Investment", "Paper", "OnDemand"
])

# Apply filters
if strategy_filter:
    data = data[data["Strategy"].isin(strategy_filter)]
if paper_only:
    data = data[data["Paper"] == True]
if ondemand_only:
    data = data[data["OnDemand"] == True]

# Format
data["Date"] = pd.to_datetime(data["Date"]).dt.strftime("%m-%d-%Y")
data["Return %"] = data["Return %"].round(2)
data["Gain/Loss"] = data["Gain/Loss"].round(2)
data["Total Investment"] = data["Total Investment"].round(2)

st.subheader("📋 Trade History")
st.dataframe(data)

# CSV Export
csv = data.to_csv(index=False)
st.download_button("📥 Download CSV", data=csv, file_name="trades_export.csv", mime="text/csv")

# -------------------------------
# 🗑️ Delete Trade
# -------------------------------
with st.expander("🗑️ Delete Trade by ID"):
    delete_id = st.number_input("Enter Trade ID to delete", step=1)
    if st.button("Delete Trade"):
        run_query("DELETE FROM trades WHERE id = %s", (delete_id,))
        st.success(f"Trade with ID {delete_id} deleted.")

# -------------------------------
# 📆 Weekly Summary
# -------------------------------
st.subheader("📅 Weekly Summary")
data["Week"] = pd.to_datetime(data["Date"]).dt.isocalendar().week
summary = data.groupby("Week")[["Gain/Loss", "Return %"]].agg(["sum", "mean"]).round(2)
st.dataframe(summary)

# -------------------------------
# 📌 Scaling Plan & Notes
# -------------------------------
st.info("""
**📌 Reminder:** Did you follow your scaling plan and stop-loss rule?
- Scale Out: 25% at 1st target, 50% at 2nd target, 25% at final target
- Stop-Loss Adjusted After Entry? ✅
""")
