import sqlite3

conn = sqlite3.connect("inventory.db")
cur = conn.cursor()

# products テーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    category        TEXT,
    item_name       TEXT NOT NULL,
    stock_qty       INTEGER NOT NULL DEFAULT 0,
    min_stock_qty   INTEGER NOT NULL DEFAULT 0
);
""")

# transaction_types テーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS transaction_types (
    type_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name   TEXT NOT NULL
);
""")

# users テーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name   TEXT NOT NULL,
    password    TEXT NOT NULL
);
""")

# stock_movements テーブル
cur.execute("""
CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL,
    type_id     INTEGER NOT NULL,
    datetime    TEXT NOT NULL,
    user_id     INTEGER NOT NULL,
    quantity    INTEGER NOT NULL,
    FOREIGN KEY(product_id) REFERENCES products(product_id),
    FOREIGN KEY(type_id) REFERENCES transaction_types(type_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
""")

# 初期データ（例：入庫=1, 出庫=2）
cur.execute("INSERT INTO transaction_types (type_name) VALUES (?)", ("入庫",))
cur.execute("INSERT INTO transaction_types (type_name) VALUES (?)", ("出庫",))

# テスト用ユーザー
cur.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", ("admin", "password"))

conn.commit()
conn.close()

print("DB 作成完了")
