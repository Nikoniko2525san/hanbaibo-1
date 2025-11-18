from flask import Flask, request, render_template, send_file, redirect
import sqlite3, os, io, qrcode, random, string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
DB = "data.db"

# DB作成
def init_db():
    if not os.path.exists(DB):
        conn = sqlite3.connect(DB)
        conn.execute("""
            CREATE TABLE cards(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT,
                date TEXT,
                cost INTEGER,
                price INTEGER,
                shipped INTEGER,
                rarity TEXT
            )
        """)
        conn.commit()
        conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ① コード大量生成（PDF）
@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":
        amount = int(request.form["amount"])
        codes = []
        for _ in range(amount):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            codes.append(code)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        x, y = 50, 800
        for code in codes:
            c.drawString(x, y, code)
            y -= 20
            if y < 50:
                c.showPage()
                y = 800
        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="codes.pdf")

    return render_template("generate.html")

# ② カメラスキャナー
@app.route("/scanner")
def scanner():
    return render_template("scanner.html")

# ③ 新規登録
@app.route("/register/<code>", methods=["GET", "POST"])
def register(code):
    conn = get_db()
    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        cost = request.form["cost"]
        price = request.form["price"]
        shipped = int(request.form.get("shipped", 0))
        rarity = request.form["rarity"]

        conn.execute(
            "INSERT INTO cards (code,name,date,cost,price,shipped,rarity) VALUES (?,?,?,?,?,?,?)",
            (code, name, date, cost, price, shipped, rarity)
        )
        conn.commit()
        return redirect(f"/card/{code}")

    return render_template("register.html", code=code)

# ④ カード表示・編集
@app.route("/card/<code>", methods=["GET", "POST"])
def card(code):
    conn = get_db()
    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        cost = request.form["cost"]
        price = request.form["price"]
        shipped = int(request.form.get("shipped", 0))
        rarity = request.form["rarity"]

        conn.execute("""
            UPDATE cards SET name=?, date=?, cost=?, price=?, shipped=?, rarity=? WHERE code=?
        """, (name,date,cost,price,shipped,rarity,code))
        conn.commit()

    card = conn.execute("SELECT * FROM cards WHERE code=?", (code,)).fetchone()
    if not card:
        return redirect(f"/register/{code}")
    return render_template("card.html", card=card)

# ⑤ 条件検索
@app.route("/search", methods=["GET","POST"])
def search():
    query = "SELECT * FROM cards WHERE 1=1"
    params = []
    if request.method == "POST":
        name = request.form.get("name")
        rarity = request.form.get("rarity")
        shipped = request.form.get("shipped")
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if rarity:
            query += " AND rarity=?"
            params.append(rarity)
        if shipped:
            query += " AND shipped=?"
            params.append(shipped)
    conn = get_db()
    results = conn.execute(query, params).fetchall()
    return render_template("search.html", results=results)

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
