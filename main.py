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
        "limit": 50
    }

    r = requests.get(url, params=params).json()

    if "result" not in r or "list" not in r["result"]:
        raise Exception("Bybit API error")

    data = r["result"]["list"]

    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume","turnover"
    ])

    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


def run_bot():
    print("RUN_BOT EXECUTED")
    send_telegram("🚀 Bot 已啟動")

    while True:
        try:
            for symbol in SYMBOLS:
                df = get_klines(symbol)

                high_now = df["high"].iloc[-1]
                high_prev = df["high"].iloc[-2]

                low_now = df["low"].iloc[-1]
                low_prev = df["low"].iloc[-2]

                close_now = df["close"].iloc[-1]
                close_prev = df["close"].iloc[-2]

                volume_now = df["volume"].iloc[-1]
                volume_prev = df["volume"].iloc[-2]

                # 🔥 測試訊號（一定會發）
                send_telegram(f"🧪 {symbol} 已成功抓到資料")

                # 📈 真策略
                if high_now > high_prev:
                    send_telegram(f"📈 {symbol} 創新高")

                if low_now < low_prev:
                    send_telegram(f"📉 {symbol} 破低")

                if close_now > close_prev * 1.002:
                    send_telegram(f"🚀 {symbol} 強勢上漲")

                if close_now < close_prev * 0.998:
                    send_telegram(f"⚠️ {symbol} 強勢下跌")

                if volume_now > volume_prev * 1.3:
                    send_telegram(f"🔥 {symbol} 成交量爆發")

            print("Checked at", datetime.now())

        except Exception as e:
            print("Bot error:", e)
            send_telegram(f"❌ Bot error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
