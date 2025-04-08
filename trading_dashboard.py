import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
from config import DB_CONFIG

# ----- Page Config (must be FIRST!) -----
st.set_page_config(page_title="Trading Dashboard", layout="wide")

# --- Optional Basic Password Protection ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "zoran123":  # ✅ Change your secret password here
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😅 Wrong password.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- Database Connection ---
@st.cache_resource
def get_connection():
    conn = psycopg2.connect(
        host=st.secrets["host"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        dbname=st.secrets["database"],
        sslmode='require'
    )
    return conn

conn = get_connection()

# --- Load Data ---
df = pd.read_sql("SELECT * FROM trades ORDER BY trade_date, trade_time", conn)

# --- Preprocessing ---
df['trade_date'] = pd.to_datetime(df['trade_date'])
df['trade_time'] = pd.to_datetime(df['trade_time'], format='%H:%M', errors='coerce')
df['hour'] = df['trade_time'].dt.hour

# --- Function to insert trade ---
def insert_trade(data):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO trades (trade_date, trade_time, strategy, stock_symbol, position_type, shares,
        buy_price, sell_price, stop_loss_price, premarket_news, emotion, net_gain_loss, return_win, return_loss,
        return_percent, return_percent_loss, total_investment, fees, gross_return, win_flag, ira_trade)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, data)
        conn.commit()
        conn.close()
        st.success("✅ Trade submitted successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# --- Trade Entry Form ---
st.header("🚀 Enter New Trade")

with st.form("trade_form"):
    trade_date = st.date_input("Trade Date")
    trade_time = st.time_input("Trade Time")
    strategy = st.selectbox("Strategy", ["Momentum", "Gap & Go", "Reversal", "Scalp"])
    stock_symbol = st.text_input("Stock Symbol (e.g., AAPL, TSLA)").upper()
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
        st.experimental_rerun()

# --- Delete Trade by ID ---
st.header("🗑️ Delete a Trade by ID")
with st.form("delete_form"):
    trade_ids = df['id'].tolist()
    if trade_ids:
        delete_id = st.selectbox("Select Trade ID to Delete", trade_ids)
        delete_submit = st.form_submit_button("Delete Trade")

        if delete_submit:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM trades WHERE id = %s", (delete_id,))
                conn.commit()
                conn.close()
                st.success(f"✅ Trade ID {delete_id} deleted successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Error deleting trade: {e}")
    else:
        st.warning("⚠️ No trades available to delete.")

# --- Filters ---
st.sidebar.header("📊 Filters")
selected_date = st.sidebar.date_input("Select Date", datetime.now().date())
filtered_df = df[df['trade_date'].dt.date == selected_date]

# --- Daily Summary ---
st.subheader(f"📅 Daily Summary for {selected_date}")
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

# --- Checklist Status ---
st.markdown("### 📝 Checklist Status")
trade_time_check = filtered_df.shape[0] == filtered_df[(filtered_df['hour'] >= 9) & (filtered_df['hour'] <= 12)].shape[0]
st.write("- Trade in simulator only ✅")
st.write(f"- Trade between 9:30 AM and 12:00 PM: {'✅' if trade_time_check else '⚠️ Some trades outside window'}")
st.write(f"- Use approved strategies only ✅")
st.write(f"- Max 4 trades/day: {'✅' if daily_trades <= 4 else '⚠️ Exceeded!'}")
st.write(f"- Daily Max Loss: {'✅' if daily_profit > daily_max_loss else '⚠️ Hit max loss!'}")
st.write(f"- Daily Profit Target: {'✅' if daily_profit >= daily_profit_target else 'Not yet ❌'}")

# --- Export to CSV ---
st.download_button("📥 Download All Trades as CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="all_trades.csv", mime="text/csv")

# --- Main Table ---
st.subheader("🧾 All Trades")
st.dataframe(filtered_df, use_container_width=True)

# --- Emotion Tracker ---
st.subheader("😌 Emotion Tracker")
emotion_counts = filtered_df['emotion'].value_counts()
st.bar_chart(emotion_counts)

# --- Pre-Market News Impact ---
st.subheader("📰 Pre-Market News Impact")
news_impact = filtered_df['premarket_news'].value_counts()
st.bar_chart(news_impact)

# --- Profit by Strategy ---
st.subheader("💼 Profit by Strategy")
profit_by_strategy = filtered_df.groupby("strategy")["net_gain_loss"].sum().sort_values(ascending=False)
st.bar_chart(profit_by_strategy)

# --- Strategy Accuracy ---
st.subheader("📊 Strategy Win Rate")
strategy_win_rate = filtered_df.groupby("strategy")["win_flag"].mean() * 100
st.bar_chart(strategy_win_rate)

# --- Profit by Symbol ---
st.subheader("🏷️ Profit by Symbol")
profit_by_symbol = filtered_df.groupby("stock_symbol")["net_gain_loss"].sum().sort_values(ascending=False)
st.bar_chart(profit_by_symbol)

# --- Trade Time Distribution ---
st.subheader("🕰️ Trade Time Distribution")
trade_times = filtered_df['hour'].value_counts().sort_index()
st.bar_chart(trade_times)

# --- Monthly Profit ---
df['month'] = df['trade_date'].dt.to_period('M')
monthly_profit = df.groupby('month')['net_gain_loss'].sum()
st.subheader("📅 Monthly Profit")
st.bar_chart(monthly_profit)

# --- Summary KPIs ---
total_profit = df['net_gain_loss'].sum()
win_rate = df['win_flag'].mean() * 100
num_trades = len(df)

st.markdown("---")
st.subheader("📊 Key Stats")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Profit", f"${total_profit:,.2f}")
kpi2.metric("Win Rate", f"{win_rate:.1f}%")
kpi3.metric("Total Trades", f"{num_trades}")
