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

SYMBOLS = ["ETHUSDT","SOLUSDT","DOGEUSDT"]
INTERVAL = "5"
CHECK_INTERVAL = 300

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except:
        pass

# 🔥 改這裡：用 Bytick API
def get_klines(symbol):
    url = "https://api.bytick.com/v5/market/kline"

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": 200
    }

    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    data = r.json()["result"]["list"]

    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume","turnover"
    ])

    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="ms")
    df = df.sort_values("timestamp")
    df = df.astype({
        "high": float,
        "low": float,
        "close": float,
        "volume": float
    })

    return df

def run_bot():
    send_telegram("🚀 Bot 已啟動")

    while True:
        try:
            for symbol in SYMBOLS:
                df = get_klines(symbol)

                close_now = df["close"].iloc[-1]
                close_prev = df["close"].iloc[-2]

                if close_now > close_prev * 1.002:
                    send_telegram(f"🚀 {symbol} 上漲動能")

                if close_now < close_prev * 0.998:
                    send_telegram(f"⚠️ {symbol} 下跌動能")

            print("Checked", datetime.now())

        except Exception as e:
            send_telegram(f"❌ Bot error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
