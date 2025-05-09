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
