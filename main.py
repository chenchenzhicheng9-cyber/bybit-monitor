from flask import Flask
import threading
import requests
import pandas as pd
import time
from datetime import datetime
import os

# ===== Flask 假網站 (Render 保持活著) =====
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
CHECK_INTERVAL = 60   # 每1分鐘檢查一次

# ===== Telegram 發送 =====
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram error:", e)

# ===== 取得 K線 =====
def get_klines(symbol):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": 20
    }

    r = requests.get(url, params=params, timeout=10)

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    try:
        data_json = r.json()
    except:
        raise Exception("API 回傳非 JSON")

    if data_json.get("retCode") != 0:
        raise Exception(f"Bybit錯誤: {data_json}")

    data = data_json["result"]["list"]

    df = pd.DataFrame(data, columns=[
        "timestamp","open","high","low","close","volume","turnover"
    ])

    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df

# ===== 市場監控 =====
last_alert = {}

def check_market(symbol, df):
    close_now = df["close"].iloc[-1]
    close_prev = df["close"].iloc[-2]

    high_now = df["high"].iloc[-1]
    high_prev = df["high"].iloc[-2]

    low_now = df["low"].iloc[-1]
    low_prev = df["low"].iloc[-2]

    vol_now = df["volume"].iloc[-1]
    vol_prev = df["volume"].iloc[-2]

    msg = None

    # ===== 強勢波動 =====
    if close_now > close_prev * 1.002:
        msg = f"🚀 {symbol} 強勢上漲K"

    elif close_now < close_prev * 0.998:
        msg = f"⚠️ {symbol} 強勢下跌K"

    # ===== 突破 =====
    elif high_now > high_prev:
        msg = f"📈 {symbol} 創短線新高"

    elif low_now < low_prev:
        msg = f"📉 {symbol} 跌破短線低點"

    # ===== 量能爆發 =====
    elif vol_now > vol_prev * 1.8:
        msg = f"🔥 {symbol} 成交量爆發"

    # ===== 防重複通知 =====
    if msg:
        last = last_alert.get(symbol)
        if last != msg:
            send_telegram(msg)
            last_alert[symbol] = msg

# ===== 主監控程式 =====
def run_bot():
    print("BOT START")
    send_telegram("🚀 Bot 已啟動，市場監控開始")

    while True:
        try:
            for symbol in SYMBOLS:
                df = get_klines(symbol)
                check_market(symbol, df)

            print("Checked at", datetime.now())

        except Exception as e:
            send_telegram(f"❌ Bot error: {e}")
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

# ===== Render 啟動入口 =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
