from flask import Flask
import threading
import requests
import pandas as pd
import time
from datetime import datetime
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

TELEGRAM_TOKEN = "8602049522:AAF91zldayTlXuoBtMKskpC0vR123zk-Ftw"
CHAT_ID = "8132526624"

SYMBOLS = ["ETHUSDT", "SOLUSDT", "DOGEUSDT"]
INTERVAL = "5"
CHECK_INTERVAL = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

def get_klines(symbol):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": 20
    }

    r = requests.get(url, params=params, headers=HEADERS, timeout=10)

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    try:
        data_json = r.json()
    except:
        raise Exception("Bybit回傳非JSON")

    if data_json.get("retCode") != 0:
        raise Exception(data_json)

    data = data_json["result"]["list"]

    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume","turnover"
    ])

    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

last_alert = {}

def check_market(symbol, df):
    c = df["close"].iloc[-1]
    p = df["close"].iloc[-2]
    h = df["high"].iloc[-1]
    hp = df["high"].iloc[-2]
    l = df["low"].iloc[-1]
    lp = df["low"].iloc[-2]
    v = df["volume"].iloc[-1]
    vp = df["volume"].iloc[-2]

    msg = None

    if c > p * 1.002:
        msg = f"🚀 {symbol} 上漲K"
    elif c < p * 0.998:
        msg = f"⚠️ {symbol} 下跌K"
    elif h > hp:
        msg = f"📈 {symbol} 新高"
    elif l < lp:
        msg = f"📉 {symbol} 新低"
    elif v > vp * 1.8:
        msg = f"🔥 {symbol} 爆量"

    if msg and last_alert.get(symbol) != msg:
        send_telegram(msg)
        last_alert[symbol] = msg

def run_bot():
    print("BOT START")
    send_telegram("🚀 Bot 已啟動")

    while True:
        try:
            for s in SYMBOLS:
                df = get_klines(s)
                check_market(s, df)

            print("Checked", datetime.now())

        except Exception as e:
            send_telegram(f"❌ Bot error: {e}")
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

