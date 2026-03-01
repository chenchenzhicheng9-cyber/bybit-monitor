from flask import Flask
import threading
import requests
import pandas as pd
import time
from datetime import datetime
import pytz
import os

# ===== Flask 假網站 (給 Render 用) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

# ===== Telegram 設定 =====
TELEGRAM_TOKEN = "8602049522:AAF91zldayTlXuoBtMKskpC0vR123zk-Ftw"
CHAT_ID = "8132526624"

# ===== 交易設定 =====
SYMBOLS = ["ETHUSDT", "SOLUSDT", "DOGEUSDT"]
INTERVAL = "5"
CHECK_INTERVAL = 300

tz = pytz.timezone("Asia/Taipei")

# ===== Telegram 發送 =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

# ===== 取得 K線 (已修403問題) =====
def get_klines(symbol):
    url = "https://api.bybit.com/v5/market/kline"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": 200
    }

    r = requests.get(url, params=params, headers=headers, timeout=10)

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

# ===== 主監控程式 =====
def run_bot():
    send_telegram("🚀 Bot 已啟動，市場監控開始")

    last_test = 0

    while True:
        try:
            # ===== Bot 在線確認 =====
            now = time.time()
            if now - last_test > 300:
                send_telegram("🧪 Bot 在線中")
                last_test = now

            # ===== 三幣監控 =====
            for symbol in SYMBOLS:
                df = get_klines(symbol)

                close_now = df["close"].iloc[-1]
                close_prev = df["close"].iloc[-2]

                high_now = df["high"].iloc[-1]
                high_prev = df["high"].iloc[-2]

                low_now = df["low"].iloc[-1]
                low_prev = df["low"].iloc[-2]

                volume_now = df["volume"].iloc[-1]
                volume_prev = df["volume"].iloc[-2]

                # ===== 市場活動提醒 =====
                if close_now > close_prev * 1.002:
                    send_telegram(f"🚀 {symbol} 上漲動能出現")

                if close_now < close_prev * 0.998:
                    send_telegram(f"⚠️ {symbol} 下跌動能出現")

                if high_now > high_prev:
                    send_telegram(f"📈 {symbol} 創短線新高")

                if low_now < low_prev:
                    send_telegram(f"📉 {symbol} 跌破短線低點")

                if volume_now > volume_prev * 1.4:
                    send_telegram(f"🔥 {symbol} 成交量放大")

            print("Checked at", datetime.now())

        except Exception as e:
            send_telegram(f"❌ Bot error: {e}")

        time.sleep(CHECK_INTERVAL)

# ===== Render 啟動入口 =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
