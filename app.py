from flask import Flask, render_template, request, redirect, url_for, session, abort
from functools import wraps
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret-key"  # 本番ではもっと長いランダム文字列にしてください

DB_PATH = "inventory.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 辞書的にアクセスできるようにする
    return conn

def login_required(func):
    # 簡易デコレータ（ログインチェック）
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    # ログインしていれば products へ、していなければ login へ
    if "user_id" in session:
        return redirect(url_for("products"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user_name = request.form["user_name"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE user_name = ? AND password = ?",
            (user_name, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["user_id"]
            session["user_name"] = user["user_name"]
            return redirect(url_for("products"))
        else:
            error = "ユーザー名またはパスワードが違います。"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/products")
@login_required
def products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT product_id, category, item_name, stock_qty, min_stock_qty
        FROM products
        ORDER BY category, item_name
    """)
    products = cur.fetchall()
    conn.close()

    return render_template("products.html", products=products)

@app.route("/stock_move", methods=["GET", "POST"])
@login_required
def stock_move():
    conn = get_db_connection()
    cur = conn.cursor()

    # プルダウン用に商品一覧と取引種別一覧を取得
    cur.execute("SELECT product_id, item_name FROM products ORDER BY item_name")
    products = cur.fetchall()

    cur.execute("SELECT type_id, type_name FROM transaction_types ORDER BY type_id")
    types = cur.fetchall()

    message = None
    error = None

    if request.method == "POST":
        product_id = request.form.get("product_id")
        type_id = request.form.get("type_id")
        qty = request.form.get("quantity")

        try:
            qty = int(qty)
        except:
            error = "数量は整数で入力してください。"
            return render_template("stock_move.html",
                                   products=products, types=types,
                                   error=error, message=message)

        # 在庫更新ロジック
        try:
            conn.execute("BEGIN")  # トランザクション開始（同時利用への基本対策）

            # 現在の在庫取得
            cur.execute("SELECT stock_qty FROM products WHERE product_id = ?", (product_id,))
            row = cur.fetchone()
            if not row:
                raise Exception("対象の商品が存在しません。")

            current_stock = row["stock_qty"]

            # type_id によって符号を変える（1=入庫, 2=出庫 という前提）
            if int(type_id) == 1:  # 入庫
                new_stock = current_stock + qty
            elif int(type_id) == 2:  # 出庫
                new_stock = current_stock - qty
                if new_stock < 0:
                    raise Exception("在庫がマイナスになります。")
            else:
                raise Exception("不明な取引種別です。")

            # products 更新
            cur.execute("""
                UPDATE products
                SET stock_qty = ?
                WHERE product_id = ?
            """, (new_stock, product_id))

            # stock_movements に履歴追加
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO stock_movements
                    (product_id, type_id, datetime, user_id, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, type_id, now_str, session["user_id"], qty))

            conn.commit()
            message = "入出庫を登録しました。"

        except Exception as e:
            conn.rollback()
            error = f"エラーが発生しました: {e}"

    conn.close()

    return render_template("stock_move.html",
                           products=products, types=types,
                           error=error, message=message)

if __name__ == "__main__":
    app.run(debug=True)
