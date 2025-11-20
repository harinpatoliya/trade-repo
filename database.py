import sqlite3
import pandas as pd
import datetime

DB_NAME = "paper_trade.db"

def init_db():
    # We will not drop tables here to preserve data across restarts in real usage,
    # but for dev schema changes, we might need to handle migration.
    # Since this is initial dev, we can assume fresh start if schema changes.
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Create Account Table
    c.execute('''CREATE TABLE IF NOT EXISTS account (
                    id INTEGER PRIMARY KEY,
                    balance REAL
                 )''')

    # Create Holdings Table
    # Added first_buy_date
    c.execute('''CREATE TABLE IF NOT EXISTS holdings (
                    symbol TEXT,
                    exchange TEXT,
                    quantity INTEGER,
                    average_price REAL,
                    first_buy_date TIMESTAMP,
                    PRIMARY KEY (symbol, exchange)
                 )''')

    # Create Trades Table (Order History)
    c.execute('''CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    exchange TEXT,
                    order_type TEXT,
                    transaction_type TEXT,
                    quantity INTEGER,
                    price REAL,
                    date TIMESTAMP
                 )''')

    # Create Closed Positions Table (Realized P&L History)
    c.execute('''CREATE TABLE IF NOT EXISTS closed_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    buy_date TIMESTAMP,
                    buy_price REAL,
                    buy_quantity INTEGER,
                    sell_date TIMESTAMP,
                    sell_quantity INTEGER,
                    pnl REAL,
                    pnl_percent REAL
                 )''')

    # Initialize balance if not exists
    c.execute("SELECT count(*) FROM account")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO account (balance) VALUES (300000)")

    conn.commit()
    conn.close()

def reset_account():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM account")
    c.execute("DELETE FROM holdings")
    c.execute("DELETE FROM trades")
    c.execute("DELETE FROM closed_positions")
    c.execute("INSERT INTO account (balance) VALUES (300000)")
    conn.commit()
    conn.close()

def get_account():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM account", conn)
    conn.close()
    if df.empty:
        return {'balance': 0}
    return df.iloc[0]

def get_holdings():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM holdings", conn)
    conn.close()
    return df

def get_history():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM closed_positions ORDER BY sell_date DESC", conn)
    conn.close()
    return df

def buy_stock(symbol, exchange, quantity, price, order_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Check balance
    c.execute("SELECT balance FROM account")
    res = c.fetchone()
    balance = res[0] if res else 0
    cost = quantity * price

    if balance < cost:
        conn.close()
        return False, "Insufficient funds"

    # Deduct balance
    new_balance = balance - cost
    c.execute("UPDATE account SET balance = ?", (new_balance,))

    # Update Holdings
    c.execute("SELECT quantity, average_price, first_buy_date FROM holdings WHERE symbol = ? AND exchange = ?", (symbol, exchange))
    row = c.fetchone()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if row:
        old_qty = row[0]
        old_avg = row[1]
        # keep original first_buy_date

        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
        c.execute("UPDATE holdings SET quantity = ?, average_price = ? WHERE symbol = ? AND exchange = ?", (new_qty, new_avg, symbol, exchange))
    else:
        c.execute("INSERT INTO holdings (symbol, exchange, quantity, average_price, first_buy_date) VALUES (?, ?, ?, ?, ?)",
                  (symbol, exchange, quantity, price, now_str))

    # Log Trade
    c.execute("INSERT INTO trades (symbol, exchange, order_type, transaction_type, quantity, price, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (symbol, exchange, order_type, "BUY", quantity, price, now_str))

    conn.commit()
    conn.close()
    return True, f"Bought {quantity} of {symbol} at {price}"

def sell_stock(symbol, exchange, quantity, price, order_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Check holdings
    c.execute("SELECT quantity, average_price, first_buy_date FROM holdings WHERE symbol = ? AND exchange = ?", (symbol, exchange))
    row = c.fetchone()

    if not row or row[0] < quantity:
        conn.close()
        return False, "Insufficient holdings"

    holding_qty = row[0]
    avg_price = row[1]
    first_buy_date = row[2]

    # Update Holdings
    new_qty = holding_qty - quantity
    if new_qty == 0:
        c.execute("DELETE FROM holdings WHERE symbol = ? AND exchange = ?", (symbol, exchange))
    else:
        # Average price remains same on sell
        c.execute("UPDATE holdings SET quantity = ? WHERE symbol = ? AND exchange = ?", (new_qty, symbol, exchange))

    # Credit Balance
    revenue = quantity * price
    c.execute("SELECT balance FROM account")
    balance = c.fetchone()[0]
    c.execute("UPDATE account SET balance = ?", (balance + revenue,))

    # Log Trade
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO trades (symbol, exchange, order_type, transaction_type, quantity, price, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (symbol, exchange, order_type, "SELL", quantity, price, now_str))

    # Log Closed Position
    pnl = (price - avg_price) * quantity
    pnl_percent = ((price - avg_price) / avg_price) * 100 if avg_price else 0

    c.execute('''INSERT INTO closed_positions (symbol, buy_date, buy_price, buy_quantity, sell_date, sell_quantity, pnl, pnl_percent)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (symbol, first_buy_date, avg_price, quantity, now_str, quantity, pnl, pnl_percent))

    conn.commit()
    conn.close()
    return True, f"Sold {quantity} of {symbol} at {price}"
