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
TELEGRAM_TOKEN = "你的TOKEN"
CHAT_ID = "你的CHATID"

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
        r = requests.post(url, data=data)
        print("Telegram:", r.text)
    except Exception as e:
        print("Telegram error:", e)

# ===== 取得 Bybit K線 =====
def get_klines(symbol):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": 200
    }
    r = requests.get(url, params=params).json()
    data = r["result"]["list"]

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

# ===== SMT 背離 =====
def check_smt(df_dict):
    try:
        eth = df_dict["ETHUSDT"]
        sol = df_dict["SOLUSDT"]

        eth_high = eth["high"].iloc[-1]
        eth_prev = eth["high"].iloc[-2]

        sol_high = sol["high"].iloc[-1]
        sol_prev = sol["high"].iloc[-2]

        if eth_high > eth_prev and sol_high <= sol_prev:
            send_telegram("⚠️ SMT Bearish：ETH創高但SOL沒創")

    except:
        pass

# ===== 主監控程式 =====
def run_bot():
    print("RUN_BOT EXECUTED")
    send_telegram("🚀 Bot 已啟動，市場監控開始")

    last_test_time = 0

    while True:
        try:
            # ===== 每5分鐘確認 Bot 活著 =====
            now = time.time()
            if now - last_test_time > 300:
                send_telegram("🧪 Bot 在線中")
                last_test_time = now

            df_dict = {}

            for symbol in SYMBOLS:
                df = get_klines(symbol)
                df_dict[symbol] = df

                high_now = df["high"].iloc[-1]
                high_prev = df["high"].iloc[-2]

                low_now = df["low"].iloc[-1]
                low_prev = df["low"].iloc[-2]

                close_now = df["close"].iloc[-1]
                close_prev = df["close"].iloc[-2]

                volume_now = df["volume"].iloc[-1]
                volume_prev = df["volume"].iloc[-2]

                # ===== 市場活動提醒 =====

                if close_now > close_prev * 1.001:
                    send_telegram(f"🚀 {symbol} 強勢上漲K")

                if close_now < close_prev * 0.999:
                    send_telegram(f"⚠️ {symbol} 強勢下跌K")

                if high_now > high_prev:
                    send_telegram(f"📈 {symbol} 創短線新高")

                if low_now < low_prev:
                    send_telegram(f"📉 {symbol} 跌破短線低點")

                if volume_now > volume_prev * 1.3:
                    send_telegram(f"🔥 {symbol} 成交量爆發")

            # SMT 背離
            check_smt(df_dict)

            print("Checked at", datetime.now())

        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

# ===== Render 啟動入口 =====
if __name__ == "__main__":
    print("BOT START")
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
