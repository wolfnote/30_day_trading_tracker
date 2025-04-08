import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# ----- Page Config -----
st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📈 Trading Tracker Dashboard")

import psycopg2

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

# ----- Load Data -----
df = pd.read_sql("SELECT * FROM trades ORDER BY trade_date, trade_time", conn)

# ----- Preprocessing -----
df['trade_date'] = pd.to_datetime(df['trade_date'])
df['trade_time'] = pd.to_datetime(df['trade_time'], format='%H:%M', errors='coerce')
df['hour'] = df['trade_time'].dt.hour

# ----- Filters -----
st.sidebar.header("📊 Filters")
selected_date = st.sidebar.date_input("Select Date", datetime.now().date())
filtered_df = df[df['trade_date'].dt.date == selected_date]

# ----- Daily Summary -----
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

# ----- Checklist Status -----
st.markdown("### 📝 Checklist Status")
trade_time_check = filtered_df.shape[0] == filtered_df[(filtered_df['hour'] >= 9) & (filtered_df['hour'] <= 12)].shape[0]

st.write("- Trade in simulator only ✅")
st.write(f"- Trade between 9:30 AM and 12:00 PM: {'✅' if trade_time_check else '⚠️ Some trades outside window'}")
st.write(f"- Use approved strategies only ✅")
st.write(f"- Max 4 trades/day: {'✅' if daily_trades <= 4 else '⚠️ Exceeded!'}")
st.write(f"- Daily Max Loss: {'✅' if daily_profit > daily_max_loss else '⚠️ Hit max loss!'}")
st.write(f"- Daily Profit Target: {'✅' if daily_profit >= daily_profit_target else 'Not yet ❌'}")

# ----- Main Table -----
st.subheader("🧾 All Trades")
st.dataframe(filtered_df, use_container_width=True)

# ----- Emotion Tracker -----
st.subheader("😌 Emotion Tracker")
emotion_counts = filtered_df['emotion'].value_counts()
st.bar_chart(emotion_counts)

# ----- Pre-Market News Impact -----
st.subheader("📰 Pre-Market News Impact")
news_impact = filtered_df['premarket_news'].value_counts()
st.bar_chart(news_impact)

# ----- Profit by Strategy -----
st.subheader("💼 Profit by Strategy")
profit_by_strategy = filtered_df.groupby("strategy")["net_gain_loss"].sum().sort_values(ascending=False)
st.bar_chart(profit_by_strategy)

# ----- Trade Time Distribution -----
st.subheader("🕰️ Trade Time Distribution")
trade_times = filtered_df['hour'].value_counts().sort_index()
st.bar_chart(trade_times)

# ----- Monthly Profit -----
df['month'] = df['trade_date'].dt.to_period('M')
monthly_profit = df.groupby('month')['net_gain_loss'].sum()
st.subheader("📅 Monthly Profit")
st.bar_chart(monthly_profit)

# ----- Summary KPIs -----
total_profit = df['net_gain_loss'].sum()
win_rate = df['win_flag'].mean() * 100
num_trades = len(df)

st.markdown("---")
st.subheader("📊 Key Stats")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Profit", f"${total_profit:,.2f}")
kpi2.metric("Win Rate", f"{win_rate:.1f}%")
kpi3.metric("Total Trades", f"{num_trades}")
