from flask import Flask
import requests
import time
import threading
import os

# ===== Flask 保持 Render 活著 =====
app = Flask(__name__)

@app.route("/")
def home():
    return "News bot running"

# ===== Telegram 設定 =====
TOKEN = "8602049522:AAF91zldayTlXuoBtMKskpC0vR123zk-Ftw"
CHAT_ID = "8132526624"

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except:
        pass

# ===== 避免重複通知 =====
sent_news = set()

# ===== 抓 Crypto 市場新聞 =====
def fetch_crypto_news():
    url = "https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true"
    r = requests.get(url, timeout=10).json()

    alerts = []
    for post in r["results"][:10]:
        title = post["title"]

        # 過濾重要關鍵字
        keywords = [
            "ETF","SEC","Ban","Regulation","Hack","Bank",
            "Inflation","Interest","War","Fed","Rate",
            "Gold","Crisis","Liquidity"
        ]

        if any(k.lower() in title.lower() for k in keywords):
            if title not in sent_news:
                alerts.append(title)
                sent_news.add(title)

    return alerts

# ===== 抓總經新聞 =====
def fetch_macro_news():
    url = "https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey=demo"
    # demo key會有些限制，但能測試

    try:
        r = requests.get(url, timeout=10).json()
    except:
        return []

    alerts = []
    if "articles" in r:
        for art in r["articles"][:5]:
            title = art["title"]
            if title not in sent_news:
                alerts.append(title)
                sent_news.add(title)

    return alerts

# ===== 主循環 =====
def run_bot():
    send("📡 情報Bot已啟動")

    while True:
        try:
            crypto_news = fetch_crypto_news()
            macro_news = fetch_macro_news()

            for news in crypto_news:
                send(f"🪙 Crypto重大消息:\n{news}")

            for news in macro_news:
                send(f"🌍 總經消息:\n{news}")

        except Exception as e:
            send(f"❌ 情報Bot錯誤: {e}")

        time.sleep(1800)  # 每30分鐘

# ===== Render 啟動 =====
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
