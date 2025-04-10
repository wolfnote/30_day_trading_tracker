import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# -------------------------------
# 🌟 USER SETTINGS (login)
# -------------------------------
USERNAME = "wolfnote"
PASSWORD = "Beograd!98o"

# -------------------------------
# 🔌 Database Connection (Unified run_query)
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
# 🌓 Dark Mode Toggle
# -------------------------------
def set_theme():
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    dark_mode = st.sidebar.checkbox("🌓 Dark Mode", value=st.session_state["dark_mode"])
    st.session_state["dark_mode"] = dark_mode

    if dark_mode:
        st.markdown("""
            <style>
            body, .stApp { background-color: #000000; color: #e0e0e0; }
            input, textarea, select, .stButton>button {
                background-color: #333333; color: #e0e0e0; border: 1px solid #4a4a4a;
            }
            .stButton>button:hover { background-color: #555555; color: #ffffff; }
            .stCheckbox>label, .css-16huue1, .css-1aumxhk, .css-1v0mbdj { color: #e0e0e0; }
            </style>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body, .stApp { background-color: #0a192f; color: #e0e0e0; }
            input, textarea, select, .stButton>button {
                background-color: #d9d9d9; color: #000000; border: 1px solid #4a4a4a;
            }
            .stButton>button:hover { background-color: #bfbfbf; color: #000000; }
            .stCheckbox>label, .css-16huue1, .css-1aumxhk, .css-1v0mbdj { color: #e0e0e0; }
            </style>
            """, unsafe_allow_html=True)

# -------------------------------
# 🔒 Simple Login
# -------------------------------
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        with st.form("login_form"):
            st.subheader("🔒 Login")
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if username_input == USERNAME and password_input == PASSWORD:
                    st.session_state["logged_in"] = True
                    st.success("✅ Login successful! Please continue below.")
                else:
                    st.error("❌ Invalid credentials")
        return False
    return True

# -------------------------------
# 📥 Insert Trade
# -------------------------------
def insert_trade(data):
    try:
        insert_query = """
        INSERT INTO trades (
            trade_date, trade_time, strategy, stock_symbol, position_type, shares,
            buy_price, sell_price, stop_loss_price, premarket_news, emotion,
            net_gain_loss, return_win, return_loss, return_percent, return_percent_loss,
            total_investment, fees, gross_return, win_flag, ira_trade, paper_trade, ondemand_trade
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        run_query(insert_query, data)
        st.success("✅ Trade submitted successfully!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error: {e}")

# -------------------------------
# 🗑️ Delete Trade
# -------------------------------
def delete_trade(trade_id):
    try:
        delete_query = "DELETE FROM trades WHERE id = %s"
        run_query(delete_query, (trade_id,))
        st.success(f"✅ Trade ID {trade_id} deleted successfully!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error deleting trade: {e}")

# -------------------------------
# 🚀 App Main
# -------------------------------
# ✅ RRR Calculator - Add this to your trading_dashboard.py under App Main

# Existing run_query() and other functions remain intact ✅

# -------------------------------
# 🚀 App Main (Extended with RRR Calculator Tab)
# -------------------------------
st.set_page_config(page_title="Trading Dashboard", layout="wide")
set_theme()

if check_login():
    st.title("📈 Trading Tracker Dashboard")

    tab1, tab2 = st.tabs(["📊 Dashboard", "🧮 RRR Calculator"])

    # === TAB 1: Main Dashboard (Your existing code remains in tab1) === #
    with tab1:
        df = pd.DataFrame(
            run_query("SELECT * FROM trades ORDER BY trade_date, trade_time"),
            columns=["id", "trade_date", "trade_time", "strategy", "stock_symbol", "position_type", "shares",
                     "buy_price", "sell_price", "stop_loss_price", "premarket_news", "emotion",
                     "net_gain_loss", "return_win", "return_loss", "return_percent", "return_percent_loss",
                     "total_investment", "fees", "gross_return", "win_flag", "ira_trade", "paper_trade", "ondemand_trade"]
        )

        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df['trade_time'] = pd.to_datetime(df['trade_time'], format='%H:%M', errors='coerce')
        df['hour'] = df['trade_time'].dt.hour

        date_range = st.sidebar.date_input("Select Date Range", [datetime.now().date(), datetime.now().date()])
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range

        # ✅ Add Paper/OnDemand filters here if desired
        filtered_df = df[(df['trade_date'].dt.date >= start_date) & (df['trade_date'].dt.date <= end_date)]

        st.subheader("🧾 All Trades")
        st.dataframe(filtered_df, use_container_width=True)

    # === TAB 2: RRR Calculator === #
    with tab2:
        st.subheader("🧮 Risk-Reward Ratio (RRR) Calculator")

        # Inputs
        col1, col2 = st.columns(2)

        with col1:
            account_balance = st.number_input("Account Balance ($)", value=10000.0, format="%.2f")
            risk_percent = st.slider("Risk per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.1)
            entry_price = st.number_input("Entry Price ($)", value=100.0, format="%.2f")

        with col2:
            stop_loss_price = st.number_input("Stop-Loss Price ($)", value=98.0, format="%.2f")
            target_price = st.number_input("Target Price ($)", value=106.0, format="%.2f")

        # Calculations (live)
        risk_per_trade = account_balance * (risk_percent / 100)
        risk_per_share = entry_price - stop_loss_price
        potential_reward = target_price - entry_price

        if risk_per_share > 0:
            position_size = risk_per_trade / risk_per_share
            total_investment = position_size * entry_price
            max_loss = position_size * risk_per_share
            potential_profit = position_size * potential_reward
            rrr = potential_reward / risk_per_share
        else:
            position_size = total_investment = max_loss = potential_profit = rrr = 0

        # Display results
        st.markdown("### 🧩 Calculation Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Risk per Share ($)", f"{risk_per_share:.2f}")
        col2.metric("Potential Reward ($)", f"{potential_reward:.2f}")
        col3.metric("RRR", f"1:{rrr:.2f}")

        col1.metric("Position Size (shares)", f"{position_size:.0f}")
        col2.metric("Total Investment ($)", f"{total_investment:.2f}")
        col3.metric("Max Potential Loss ($)", f"{max_loss:.2f}")

        # Confirmation check ✅
        if max_loss > 0 and abs(max_loss - risk_per_trade) <= 0.01:
            st.success("✅ Risk Check Passed: Maximum Loss matches Risk per Trade")
        else:
            st.warning("⚠️ Risk Check: Please review your stop-loss or account risk inputs.")

        st.markdown("---")
        st.info("📌 Pro Tip: Aim for at least 1:2 or better RRR for high-probability setups!")

    st.markdown("✅ Dashboard and RRR Calculator are fully operational!")
