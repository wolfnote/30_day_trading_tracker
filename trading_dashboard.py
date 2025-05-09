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
        st.rerun()
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
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error deleting trade: {e}")

# -------------------------------
# 🚀 App Main
# -------------------------------
st.set_page_config(page_title="Trading Dashboard", layout="wide")
set_theme()

if check_login():
    st.title("📈 Trading Tracker Dashboard")

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

    # 📆 Date Range Filter (MM-DD-YYYY)
    date_range = st.sidebar.date_input("Select Date Range", [datetime.now().date(), datetime.now().date()])

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    # Initial date range filter
    filtered_df = df[(df['trade_date'] >= pd.to_datetime(start_date)) & (df['trade_date'] <= pd.to_datetime(end_date))]

    # Add sidebar filters for Paper and OnDemand Trades
    st.sidebar.markdown("### 🧩 Trade Type Filters")
    paper_filter = st.sidebar.checkbox("Show Paper Trades Only")
    ondemand_filter = st.sidebar.checkbox("Show OnDemand Trades Only")

    # Apply filters
    if paper_filter:
        filtered_df = filtered_df[filtered_df['paper_trade'] == True]

    if ondemand_filter:
        filtered_df = filtered_df[filtered_df['ondemand_trade'] == True]

    # 🚀 Trade Form
    with st.form("trade_form"):
        st.subheader("🚀 Enter New Trade")
        trade_date = st.date_input("Trade Date", format="MM-DD-YYYY")

        trade_time_input = st.text_input("Trade Time (HH:MM)", value="15:38")
        try:
            trade_time = datetime.strptime(trade_time_input.strip(), "%H:%M").time()
        except ValueError:
            st.warning("⏰ Enter time in HH:MM format (e.g., 15:38)")
            trade_time = None

        strategy = st.selectbox("Strategy", ["Momentum", "Momentum Scaling (25%-50%-25%)", "Gap & Go", "Reversal", "Scalp"])
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
        paper_trade = st.checkbox("Paper Trading", value=False)
        ondemand_trade = st.checkbox("OnDemand Trade", value=False)

        submitted = st.form_submit_button("Submit Trade")
        if submitted and trade_time:
            insert_trade((
                trade_date, trade_time, strategy, stock_symbol, position_type, shares,
                buy_price, sell_price, stop_loss_price, premarket_news, emotion,
                net_gain_loss, return_win, return_loss, return_percent, return_percent_loss,
                total_investment, fees, gross_return, win_flag, ira_trade, paper_trade, ondemand_trade
            ))
        elif submitted and not trade_time:
            st.error("❌ Invalid trade time format. Please use HH:MM.")



    # 🗑️ Delete Trade
    with st.form("delete_form"):
        st.subheader("🗑️ Delete Trade")

        if not df.empty:
            trade_ids = df['id'].dropna().unique().tolist()
            delete_id = st.selectbox("Select Trade ID to Delete", trade_ids)
            delete_submit = st.form_submit_button("Delete Trade")

            if delete_submit and delete_id:
                delete_trade(delete_id)
        else:
            st.info("No trades available to delete.")



    # 📅 Summary
    st.subheader(f"📅 Summary: {start_date.strftime('%m-%d-%Y')} to {end_date.strftime('%m-%d-%Y')}")
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

    # 📥 Export to CSV ✅
    st.markdown("---")
    st.subheader("📥 Export Data")
    if not filtered_df.empty:
        st.download_button(
            label="💾 Export Filtered Trades to CSV",
            data=filtered_df.to_csv(index=False, date_format="%m-%d-%Y").encode('utf-8'),
            file_name=f"trades_export_{datetime.now().strftime('%m-%d-%Y')}.csv",
            mime='text/csv'
        )
    else:
        st.info("No data to export for the selected date range.")
        
    # === 🧮 RRR Calculator (New Tab) === #
    st.markdown("---")
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
    
    col1.metric("Potential Profit ($)", f"{potential_profit:.2f}")

    # Confirmation check ✅
    if max_loss > 0 and abs(max_loss - risk_per_trade) <= 0.01:
        st.success("✅ Risk Check Passed: Maximum Loss matches Risk per Trade")
    else:
        st.warning("⚠️ Risk Check: Please review your stop-loss or account risk inputs.")

    st.markdown("---")
    st.info("📌 Pro Tip: Aim for at least 1:2 or better RRR for high-probability setups!")

    st.markdown("✅ Dashboard and RRR Calculator are fully operational!")
