import pandas as pd
import matplotlib.pyplot as plt
import psycopg2
from psycopg2 import Error
from config import DB_CONFIG
from datetime import datetime, date

# Daily tracker (reset manually or automate daily reset)
daily_trade_count = 0
daily_net_pl = 0

# Approved strategies
APPROVED_STRATEGIES = ["Gap & Go", "Momentum", "Reversals"]

# Emotion choices
EMOTION_CHOICES = ["Calm", "Rushed", "Hesitant", "Confident"]


def connect_db():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Error as e:
        print("❌ Connection error:", e)
        return None


def add_trade(cursor):
    global daily_trade_count, daily_net_pl

    if daily_trade_count >= 4:
        print("🚫 Max 4 trades reached for the day. Stop trading!")
        return

    print("\n📥 Enter trade details:")
    trade_date = input("Trade Date (YYYY-MM-DD): ")
    trade_time = input("Trade Time (HH:MM, 24h format): ")

    # Strategy validation
    print(f"Available strategies: {APPROVED_STRATEGIES}")
    strategy = input("Strategy: ")
    if strategy not in APPROVED_STRATEGIES:
        print("🚫 Invalid strategy! Use approved strategies only.")
        return

    symbol = input("Stock Symbol: ").upper()
    position = input("Position Type (Long/Short): ")

    shares = int(input("Shares: "))
    if shares > 500:
        print("🚨 Shares exceed max 500 shares limit!")
        return

    buy_price = float(input("Buy Price: "))
    sell_price = float(input("Sell Price: "))

    investment = round(buy_price * shares, 2)
    if investment > 500:
        print("🚨 Investment exceeds max $500 limit!")
        return

    stop_loss_price = float(input("Stop Loss Price: "))
    if stop_loss_price > (buy_price - 0.10):
        print("🚨 Stop loss not respecting 10¢ below entry!")
        return

    premarket_news = input("Pre-market News Impact? (yes/no): ").strip().lower()
    if premarket_news not in ["yes", "no"]:
        premarket_news = "no"  # Default to no

    print(f"Emotion choices: {EMOTION_CHOICES}")
    emotion = input("Your emotion during trade: ")
    if emotion not in EMOTION_CHOICES:
        emotion = "Calm"  # Default to Calm

    net = round((sell_price - buy_price) * shares, 2)
    win_flag = 1 if net > 0 else 0

    return_win = net if net > 0 else 0
    return_loss = net if net < 0 else 0

    return_percent = round((return_win / investment) * 100, 2) if return_win else 0
    return_percent_loss = round((return_loss / investment) * 100, 2) if return_loss else 0

    fees = 0.00
    gross_return = investment + net
    ira = int(input("IRA Trade? (1=yes, 0=no): "))

    # Daily P/L check
    daily_net_pl += net
    daily_trade_count += 1

    if daily_net_pl <= -100:
        print("🚨 Daily max loss of $100 exceeded! Stop trading!")
    elif daily_net_pl >= 200:
        print("✅ Daily profit target of $200 reached!")

    # Prepare SQL
    query = """
    INSERT INTO trades (
        trade_date, trade_time, strategy, stock_symbol, position_type, shares, buy_price, sell_price,
        stop_loss_price, premarket_news, emotion, net_gain_loss, return_win, return_loss, return_percent,
        return_percent_loss, total_investment, fees, gross_return, win_flag, ira_trade
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        trade_date, trade_time, strategy, symbol, position, shares, buy_price, sell_price,
        stop_loss_price, premarket_news, emotion, net, return_win, return_loss, return_percent,
        return_percent_loss, investment, fees, gross_return, win_flag, ira
    ))

    print("✅ Trade added successfully!")
    print(f"📊 Today's total P/L: ${daily_net_pl:.2f} | Trades: {daily_trade_count}/4")


def delete_trade(cursor):
    trade_id = input("Enter Trade ID to delete: ")
    cursor.execute("DELETE FROM trades WHERE id = %s", (trade_id,))
    print(f"🗑️ Trade {trade_id} deleted (if it existed).")


def list_trades(conn):
    df = pd.read_sql("SELECT * FROM trades ORDER BY trade_date, trade_time", conn)
    print("\n📄 All Trades:\n")
    print(df)


def show_analytics(conn):
    df = pd.read_sql("SELECT * FROM trades", conn)

    if df.empty:
        print("📭 No trades to analyze.")
        return

    print("\n📊 Performance Stats:")

    total_gain = df['net_gain_loss'].sum()
    win_rate = df['win_flag'].mean() * 100
    avg_win = df[df['net_gain_loss'] > 0]['net_gain_loss'].mean()
    avg_loss = df[df['net_gain_loss'] < 0]['net_gain_loss'].mean()

    print(f"💰 Total Gain/Loss: ${total_gain:.2f}")
    print(f"✅ Win Rate: {win_rate:.2f}%")
    print(f"📈 Average Win: ${avg_win:.2f}" if not pd.isna(avg_win) else "📈 Average Win: N/A")
    print(f"📉 Average Loss: ${avg_loss:.2f}" if not pd.isna(avg_loss) else "📉 Average Loss: N/A")

    # Monthly Profit Chart
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df['month'] = df['trade_date'].dt.to_period('M')
    monthly = df.groupby('month')['net_gain_loss'].sum()

    plt.figure(figsize=(10, 5))
    monthly.plot(kind='bar')
    plt.title("📅 Total Profit by Month")
    plt.xlabel("Month")
    plt.ylabel("Net Gain/Loss ($)")
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

    # Profit per Strategy
    strategy_profit = df.groupby('strategy')['net_gain_loss'].sum().sort_values(ascending=False)

    plt.figure(figsize=(10, 5))
    strategy_profit.plot(kind='bar', color='skyblue')
    plt.title("🔁 Profit by Strategy")
    plt.xlabel("Strategy")
    plt.ylabel("Total Net Profit ($)")
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()


def main():
    conn = connect_db()
    if conn is None:
        return

    cursor = conn.cursor()

    while True:
        print("\n📊 Trade Tracker Menu:")
        print("1. Add New Trade")
        print("2. Delete Trade")
        print("3. List All Trades")
        print("4. Exit")
        print("5. Show Analytics")
        choice = input("Select an option: ")

        if choice == '1':
            add_trade(cursor)
            conn.commit()
        elif choice == '2':
            delete_trade(cursor)
            conn.commit()
        elif choice == '3':
            list_trades(conn)
        elif choice == '4':
            break
        elif choice == '5':
            show_analytics(conn)
        else:
            print("❌ Invalid choice.")

    cursor.close()
    conn.close()
    print("🔚 Connection closed.")


if __name__ == "__main__":
    main()
