from flask import Flask
import threading
import requests
import pandas as pd
import time
from datetime import datetime
import pytz
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

tz = pytz.timezone("Asia/Taipei")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except:
        pass

# 🔥 修正：加 UA 避免 Bybit 403
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def get_klines(symbol):
    try:
        url = "https://api.bybit.com/v5/market/kline"
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": INTERVAL,
            "limit": 50
        }

        r = requests.get(url, params=params, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")

        data = r.json()

        if "result" not in data or "list" not in data["result"]:
            raise Exception("API structure error")

        df = pd.DataFrame(data["result"]["list"], columns=[
            "timestamp","open","high","low","close","volume","turnover"
        ])

        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="ms")
        df = df.sort_values("timestamp")
        df = df.astype({"high":float,"low":float,"close":float,"volume":float})

        return df

    except Exception as e:
        send_telegram(f"❌ API error {symbol}: {e}")
        return None

def run_bot():
    send_telegram("🚀 Bot 已啟動")

    while True:
        try:
            for symbol in SYMBOLS:
                df = get_klines(symbol)
                if df is None:
                    continue

                close_now = df["close"].iloc[-1]
                close_prev = df["close"].iloc[-2]

                high_now = df["high"].iloc[-1]
                high_prev = df["high"].iloc[-2]

                low_now = df["low"].iloc[-1]
                low_prev = df["low"].iloc[-2]

                volume_now = df["volume"].iloc[-1]
                volume_prev = df["volume"].iloc[-2]

                if close_now > close_prev * 1.002:
                    send_telegram(f"🚀 {symbol} 強勢上漲")

                if close_now < close_prev * 0.998:
                    send_telegram(f"⚠️ {symbol} 強勢下跌")

                if high_now > high_prev:
                    send_telegram(f"📈 {symbol} 創新高")

                if low_now < low_prev:
                    send_telegram(f"📉 {symbol} 跌破低點")

                if volume_now > volume_prev * 1.3:
                    send_telegram(f"🔥 {symbol} 成交量爆發")

        except Exception as e:
            send_telegram(f"❌ Bot crash: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
