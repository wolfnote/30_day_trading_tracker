import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
from config import DB_CONFIG

# -------------------------------
# 🌟 USER SETTINGS (login)
# -------------------------------
USERNAME = "wolfnote"
PASSWORD = "Beograd!98o"

# -------------------------------
# 🔌 Database Connection
# -------------------------------
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=st.secrets["host"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        dbname=st.secrets["database"],
        sslmode='require'
    )

# -------------------------------
# 🌓 Dark Mode Toggle
# -------------------------------
def set_theme():
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    dark_mode = st.sidebar.checkbox("🌓 Dark Mode", value=st.session_state["dark_mode"])
    st.session_state["dark_mode"] = dark_mode

    if dark_mode:
        st.markdown(
            """
            <style>
            body { background-color: #0e1117; color: #fafafa; }
            .st-bx { background-color: #262730; color: #fafafa; }
            .st-cb { background-color: #262730; color: #fafafa; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            body { background-color: white; color: black; }
            </style>
            """,
            unsafe_allow_html=True,
        )

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
                    # 🔥 Remove the rerun here
                else:
                    st.error("❌ Invalid credentials")
        return False
    return True

# -------------------------------
# 📥 Insert Trade
# -------------------------------
def insert_trade(data):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO trades (trade_date, trade_time, strategy, stock_symbol, position_type, shares,
        buy_price, sell_price, stop_loss_price, premarket_news, emotion, net_gain_loss, return_win, return_loss,
        return_percent, return_percent_loss, total_investment, fees, gross_return, win_flag, ira_trade)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, data)
        conn.commit()
        st.success("✅ Trade submitted successfully!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error: {e}")

# -------------------------------
# 🗑️ Delete Trade
# -------------------------------
def delete_trade(trade_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades WHERE id = %s", (trade_id,))
        conn.commit()
        st.success(f"✅ Trade ID {trade_id} deleted successfully!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error deleting trade: {e}")

# -------------------------------
# 🚀 App Main
# -------------------------------
st.set_page_config(page_title="Trading Dashboard", layout="wide")
set_theme()  # Apply theme

if check_login():
    st.title("📈 Trading Tracker Dashboard")

    # Load data
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM trades ORDER BY trade_date, trade_time", conn)

    # Preprocess data
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df['trade_time'] = pd.to_datetime(df['trade_time'], format='%H:%M', errors='coerce')
    df['hour'] = df['trade_time'].dt.hour

    # 📆 Date Range Filter
    st.sidebar.header("📊 Filters")
    start_date, end_date = st.sidebar.date_input("Select Date Range", [datetime.now().date(), datetime.now().date()])
    filtered_df = df[(df['trade_date'].dt.date >= start_date) & (df['trade_date'].dt.date <= end_date)]

    # 🚀 Enter New Trade
    with st.form("trade_form"):
        st.subheader("🚀 Enter New Trade")
        trade_date = st.date_input("Trade Date")
        trade_time = st.time_input("Trade Time")
        strategy = st.selectbox("Strategy", ["Momentum", "Gap & Go", "Reversal", "Scalp"])
        stock_symbol = st.text_input("Stock Symbol (e.g., AAPL, TSLA)")
        position_type = st.selectbox("Position Type", ["Long", "Short"])
        shares = st.number_input("Shares", step=1, min_value=1)
        buy_price = st.number_input("Buy Price", format="%.2f")
        sell_price = st.number_input("Sell Price", format="%.2f")
        stop_loss_price = st.number_input("Stop Loss Price", format="%.2f")
        premarket_news = st.text_input("Premarket News")
        emotion = st.selectbox("Emotion", ["Calm", "Rushed", "Confident", "Hesitant"])
        net_gain_loss = st.number_input("Net Gain/Loss", format="%.2f")
        return_win = st.number_input("Return Win", format="%.2f")
        return_loss = st.number_input("Return Loss", format="%.2f")
        return_percent = st.number_input("Return Percent", format="%.2f")
        return_percent_loss = st.number_input("Return Percent Loss", format="%.2f")
        total_investment = st.number_input("Total Investment", format="%.2f")
        fees = st.number_input("Fees", format="%.2f")
        gross_return = st.number_input("Gross Return", format="%.2f")
        win_flag = st.checkbox("Win Flag (Checked = Win)", value=True)
        ira_trade = st.checkbox("IRA Trade (Checked = Yes)", value=False)

        submitted = st.form_submit_button("Submit Trade")
        if submitted:
            insert_trade((
                trade_date, trade_time, strategy, stock_symbol, position_type, shares,
                buy_price, sell_price, stop_loss_price, premarket_news, emotion,
                net_gain_loss, return_win, return_loss, return_percent, return_percent_loss,
                total_investment, fees, gross_return, win_flag, ira_trade
            ))

    # 🗑️ Delete Trade
    with st.form("delete_form"):
        st.subheader("🗑️ Delete Trade")
        trade_ids = df['id'].tolist()
        if trade_ids:
            delete_id = st.selectbox("Select Trade ID to Delete", trade_ids)
            delete_submit = st.form_submit_button("Delete Trade")
            if delete_submit:
                delete_trade(delete_id)
        else:
            st.info("No trades available to delete.")

    # 📅 Summary
    st.subheader(f"📅 Summary: {start_date} to {end_date}")
    col1, col2, col3, col4 = st.columns(4)
    daily_profit = filtered_df['net_gain_loss'].sum()
    daily_trades = filtered_df.shape[0]
    daily_win_rate = filtered_df['win_flag'].mean() * 100 if daily_trades > 0 else 0
    daily_max_loss = -100
    daily_profit_target = 200

    col1.metric("Total P/L", f"${daily_profit:.2f}")
    col2.metric("Trades Count", daily_trades)
    col3.metric("Win Rate", f"{daily_win_rate:.1f}%")
    col4.metric("Daily Goal", "Reached ✅" if daily_profit >= daily_profit_target else "Not yet ❌")

    # 📝 Checklist
    st.markdown("### 📝 Checklist Status")
    trade_time_check = filtered_df.shape[0] == filtered_df[(filtered_df['hour'] >= 9) & (filtered_df['hour'] <= 12)].shape[0]

    st.write("- Trade in simulator only ✅")
    st.write(f"- Trade between 9:30 AM and 12:00 PM: {'✅' if trade_time_check else '⚠️ Some trades outside window'}")
    st.write(f"- Use approved strategies only ✅")
    st.write(f"- Max 4 trades/day: {'✅' if daily_trades <= 4 else '⚠️ Exceeded!'}")
    st.write(f"- Daily Max Loss: {'✅' if daily_profit > daily_max_loss else '⚠️ Hit max loss!'}")
    st.write(f"- Daily Profit Target: {'✅' if daily_profit >= daily_profit_target else 'Not yet ❌'}")

    # 🧾 All Trades
    st.subheader("🧾 All Trades")
    st.dataframe(filtered_df, use_container_width=True)

    # 📊 Charts
    st.subheader("😌 Emotion Tracker")
    st.bar_chart(filtered_df['emotion'].value_counts())

    st.subheader("📰 Pre-Market News Impact")
    st.bar_chart(filtered_df['premarket_news'].value_counts())

    st.subheader("💼 Profit by Strategy")
    st.bar_chart(filtered_df.groupby("strategy")["net_gain_loss"].sum().sort_values(ascending=False))

    st.subheader("🕰️ Trade Time Distribution")
    st.bar_chart(filtered_df['hour'].value_counts().sort_index())

    df['month'] = df['trade_date'].dt.to_period('M')
    st.subheader("📅 Monthly Profit")
    st.bar_chart(df.groupby('month')['net_gain_loss'].sum())

    # 📊 Key Stats
    st.markdown("---")
    st.subheader("📊 Key Stats")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Profit", f"${df['net_gain_loss'].sum():,.2f}")
    kpi2.metric("Win Rate", f"{df['win_flag'].mean() * 100:.1f}%")
    kpi3.metric("Total Trades", f"{len(df)}")
