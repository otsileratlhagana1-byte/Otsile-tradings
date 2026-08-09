import os, sqlite3, uuid, time
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from broker import get_broker

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "otsile_trading.db"))

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS watchlists(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      symbol TEXT NOT NULL,
      UNIQUE(user_id,symbol)
    );
    CREATE TABLE IF NOT EXISTS alerts(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      symbol TEXT NOT NULL,
      condition TEXT NOT NULL,
      price REAL NOT NULL,
      active INTEGER DEFAULT 1
    );
    """)
    if not con.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        con.execute("INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)",
                    ("admin", generate_password_hash(os.environ.get("ADMIN_PASSWORD","ChangeMe123!")),
                     datetime.now(timezone.utc).isoformat()))
    con.commit(); con.close()

init_db()

@app.context_processor
def inject():
    return {"brand":"Otsile Trading", "live": os.environ.get("LIVE_TRADING_ENABLED","false").lower()=="true"}

@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("terminal.html", username=session.get("username"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        con=db()
        u=con.execute("SELECT * FROM users WHERE username=?", (request.form["username"].strip(),)).fetchone()
        con.close()
        if u and check_password_hash(u["password_hash"], request.form["password"]):
            session["user_id"]=u["id"]; session["username"]=u["username"]
            return redirect(url_for("index"))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

def broker():
    return get_broker()

@app.get("/api/account")
def account():
    return jsonify(broker().account())

@app.get("/api/positions")
def positions():
    return jsonify(broker().positions())

@app.get("/api/orders")
def orders():
    return jsonify(broker().orders())

@app.post("/api/order")
def order():
    data=request.get_json(force=True)
    required=["symbol","side","type","qty"]
    if any(k not in data for k in required):
        return jsonify({"error":"Missing order fields"}),400
    if not os.environ.get("LIVE_TRADING_ENABLED","false").lower()=="true" and os.environ.get("BROKER_MODE","paper")!="paper":
        return jsonify({"error":"Live trading is disabled by configuration."}),403
    try:
        return jsonify(broker().place_order(data))
    except Exception as e:
        return jsonify({"error":str(e)}),400

@app.delete("/api/order/<order_id>")
def cancel_order(order_id):
    try:
        return jsonify(broker().cancel_order(order_id))
    except Exception as e:
        return jsonify({"error":str(e)}),400

@app.get("/api/quote/<symbol>")
def quote(symbol):
    try:
        return jsonify(broker().quote(symbol.upper()))
    except Exception as e:
        return jsonify({"error":str(e)}),400

@app.get("/api/history/<symbol>")
def history(symbol):
    try:
        return jsonify(broker().history(symbol.upper(), request.args.get("tf","1D")))
    except Exception as e:
        return jsonify({"error":str(e)}),400

@app.get("/api/watchlist")
def watchlist():
    con=db(); rows=con.execute("SELECT symbol FROM watchlists WHERE user_id=? ORDER BY id", (session["user_id"],)).fetchall(); con.close()
    return jsonify([r["symbol"] for r in rows])

@app.post("/api/watchlist")
def add_watch():
    s=request.get_json(force=True)["symbol"].upper()
    con=db()
    try: con.execute("INSERT OR IGNORE INTO watchlists(user_id,symbol) VALUES(?,?)",(session["user_id"],s)); con.commit()
    finally: con.close()
    return jsonify({"ok":True})

@app.delete("/api/watchlist/<symbol>")
def del_watch(symbol):
    con=db(); con.execute("DELETE FROM watchlists WHERE user_id=? AND symbol=?",(session["user_id"],symbol.upper())); con.commit(); con.close()
    return jsonify({"ok":True})

@app.get("/health")
def health(): return jsonify({"status":"ok","service":"otsile-trading"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
