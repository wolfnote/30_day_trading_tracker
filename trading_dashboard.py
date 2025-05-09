# trading_dashboard_app.py

import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

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
# 🌃 Theme
# -------------------------------
def set_theme():
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    dark_mode = st.sidebar.checkbox("🌃 Dark Mode", value=st.session_state["dark_mode"])
    st.session_state["dark_mode"] = dark_mode

    style = """
        <style>
        body, .stApp { background-color: %s; color: %s; }
        input, textarea, select, .stButton>button {
            background-color: %s; color: %s; border: 1px solid #4a4a4a;
        }
        .stButton>button:hover { background-color: #555555; color: #ffffff; }
        </style>
    """ % (
        ("#000000" if dark_mode else "#0a192f"),
        "#e0e0e0",
        ("#333333" if dark_mode else "#d9d9d9"),
        ("#e0e0e0" if dark_mode else "#000000")
    )
    st.markdown(style, unsafe_allow_html=True)

# -------------------------------
# 🔒 Login
# -------------------------------
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        with st.form("login_form"):
            st.subheader("🔒 Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if username == USERNAME and password == PASSWORD:
                    st.session_state["logged_in"] = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        return False
    return True

# -------------------------------
# 📅 Insert Trade
# -------------------------------
def insert_trade(data):
    insert_query = """
    INSERT INTO trades (
        trade_date, trade_time, strategy, stock_symbol, position_type, shares,
        buy_price, sell_price, stop_loss_price, premarket_news, emotion,
        net_gain_loss, return_win, return_loss, return_percent, return_percent_loss,
        total_investment, fees, gross_return, win_flag, ira_trade, paper_trade, ondemand_trade
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    run_query(insert_query, data)

# -------------------------------
# 🔧 Delete Tools
# -------------------------------
def delete_trade(trade_id):
    run_query("DELETE FROM trades WHERE id = %s", (trade_id,))

def delete_range(start_id, end_id):
    run_query("DELETE FROM trades WHERE id BETWEEN %s AND %s", (start_id, end_id))

def delete_all_trades():
    run_query("DELETE FROM trades")

# -------------------------------
# 📂 CSV Upload
# -------------------------------
def handle_csv_upload():
    st.subheader("📂 Import Trades from CSV")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        columns = [
            'trade_date', 'trade_time', 'strategy', 'stock_symbol', 'position_type', 'shares',
            'buy_price', 'sell_price', 'stop_loss_price', 'premarket_news', 'emotion',
            'net_gain_loss', 'return_win', 'return_loss', 'return_percent', 'return_percent_loss',
            'total_investment', 'fees', 'gross_return', 'win_flag', 'ira_trade', 'paper_trade', 'ondemand_trade'
        ]
        if not set(columns).issubset(df.columns):
            st.warning("⚠️ Missing one or more required columns.")
            return

        inserted = 0
        for i, row in df.iterrows():
            try:
                row['trade_date'] = pd.to_datetime(row['trade_date']).date()
                row['trade_time'] = datetime.strptime(str(row['trade_time']).strip(), '%H:%M').time()
                insert_trade(tuple(row[col] for col in columns))
                inserted += 1
            except Exception as e:
                st.error(f"❌ Error inserting row {i+1}: {e}")
        st.success(f"✅ Inserted {inserted} trades.")

# -------------------------------
# 🚀 MAIN APP
# -------------------------------
set_theme()
if check_login():
    st.title("📈 Trading Tracker Dashboard")
    handle_csv_upload()

    # 🔻 Delete Tools
    with st.expander("🚨 Delete Tools", expanded=False):
        with st.form("delete_tools"):
            st.subheader("🗑️ Delete Trades")
            delete_id = st.number_input("Delete by Trade ID", step=1, min_value=1)
            start_id = st.number_input("Delete Range - Start ID", step=1, min_value=1)
            end_id = st.number_input("Delete Range - End ID", step=1, min_value=start_id)
            confirm_all = st.checkbox("I understand that deleting all trades is irreversible")
            colA, colB, colC = st.columns(3)
            if colA.form_submit_button("Delete ID"):
                delete_trade(delete_id)
                st.success(f"Deleted trade ID {delete_id}")
                st.rerun()
            if colB.form_submit_button("Delete Range"):
                delete_range(start_id, end_id)
                st.success(f"Deleted IDs {start_id} to {end_id}")
                st.rerun()
            if colC.form_submit_button("Delete All") and confirm_all:
                delete_all_trades()
                st.success("Deleted ALL trades")
                st.rerun()

    # ✅ Load Data
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

    # Date Filter
    date_range = st.sidebar.date_input("🗓️ Filter Date Range", [datetime.today(), datetime.today()])
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    filtered_df = df[(df['trade_date'] >= pd.to_datetime(start_date)) & (df['trade_date'] <= pd.to_datetime(end_date))]

    if st.sidebar.checkbox("Show Paper Trades Only"):
        filtered_df = filtered_df[filtered_df['paper_trade'] == True]

    if st.sidebar.checkbox("Show OnDemand Trades Only"):
        filtered_df = filtered_df[filtered_df['ondemand_trade'] == True]

    # Summary
    st.subheader("📊 Daily Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total P/L", f"${filtered_df['net_gain_loss'].sum():.2f}")
    col2.metric("Trades", len(filtered_df))
    col3.metric("Win Rate", f"{filtered_df['win_flag'].mean() * 100:.1f}%" if not filtered_df.empty else "0%")

    # Charts
    st.subheader("📈 Charts")
    st.bar_chart(filtered_df['emotion'].value_counts())
    st.bar_chart(filtered_df['strategy'].value_counts())
    st.bar_chart(filtered_df['hour'].value_counts().sort_index())

    # Export
    st.download_button("📅 Export CSV", data=filtered_df.to_csv(index=False), file_name="trades_export.csv")
