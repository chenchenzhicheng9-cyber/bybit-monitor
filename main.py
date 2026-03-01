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
TELEGRAM_TOKEN = os.getenv("8602049522:AAF91zldayTlXuoBtMKskpC0vR123zk-Ftw")
CHAT_ID = os.getenv("8132526624")

# ===== 交易設定 =====
SYMBOLS = ["ETHUSDT", "SOLUSDT", "DOGEUSDT"]
INTERVAL = "5"
CHECK_INTERVAL = 300

ASIA_START = 8
ASIA_END = 12
LONDON_START = 14
LONDON_END = 20

tz = pytz.timezone("Asia/Taipei")
notified_levels = {}

# ===== Telegram 發送 =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        r = requests.post(url, data=data)
        print("Telegram response:", r.text)
    except Exception as e:
        print("Telegram error:", e)

# ===== 取得 K線 =====
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
    df = df.astype({"high":float,"low":float,"close":float})
    return df

# ===== 計算區間高低 =====
def get_session_high_low(df, start_hour, end_hour):
    df["hour"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert(tz).dt.hour
    session_df = df[(df["hour"] >= start_hour) & (df["hour"] < end_hour)]
    if len(session_df) == 0:
        return None, None
    return session_df["high"].max(), session_df["low"].min()

# ===== 突破檢查 =====
def check_break(symbol, df):
    asia_high, asia_low = get_session_high_low(df, ASIA_START, ASIA_END)
    london_high, london_low = get_session_high_low(df, LONDON_START, LONDON_END)
    current_price = df.iloc[-1]["close"]

    for name, high, low in [
        ("Asia", asia_high, asia_low),
        ("London", london_high, london_low)
    ]:
        if high and current_price > high:
            key = f"{symbol}_{name}_high"
            if key not in notified_levels:
                send_telegram(f"{symbol} 突破 {name} 高點 🔥")
                notified_levels[key] = True

        if low and current_price < low:
            key = f"{symbol}_{name}_low"
            if key not in notified_levels:
                send_telegram(f"{symbol} 跌破 {name} 低點 ❄️")
                notified_levels[key] = True

# ===== SMT 背離 =====
def check_smt(df_dict):
    eth = df_dict["ETHUSDT"]
    sol = df_dict["SOLUSDT"]

    eth_high = eth["high"].iloc[-1]
    sol_high = sol["high"].iloc[-1]

    eth_prev = eth["high"].iloc[-2]
    sol_prev = sol["high"].iloc[-2]

    if eth_high > eth_prev and sol_high <= sol_prev:
        send_telegram("SMT Bearish Divergence ⚠️ ETH創高 SOL未創高")

# ===== 主監控程式 =====
def run_bot():
    send_telegram("🚀 Bot 已啟動，策略監控開始")
    while True:
        try:
            df_data = {}
            for symbol in SYMBOLS:
                df = get_klines(symbol)
                df_data[symbol] = df
                check_break(symbol, df)

            check_smt(df_data)
            print("Checked at", datetime.now())

        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

# ===== Render 啟動入口 =====
if __name__ == "__main__":
    print("Bot starting...")
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
