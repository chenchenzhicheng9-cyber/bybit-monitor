from flask import Flask
import requests
import threading
import time
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route("/")
def home():
    return "News bot running"

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

sent_news = set()

# RSS新聞源（完全公開）
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.investing.com/rss/news_25.rss"
]

def fetch_news():
    alerts = []

    for url in RSS_FEEDS:
        try:
            r = requests.get(url, timeout=10)
            root = ET.fromstring(r.content)

            for item in root.findall(".//item")[:10]:
                title = item.find("title").text

                keywords = [
                    "ETF","SEC","Fed","Rate","Inflation",
                    "War","Ban","Crisis","Liquidity","Gold"
                ]

                if any(k.lower() in title.lower() for k in keywords):
                    if title not in sent_news:
                        alerts.append(title)
                        sent_news.add(title)

        except:
            pass

    return alerts

def run_bot():
    send("📡 情報Bot啟動（RSS版本）")

    while True:
        try:
            news = fetch_news()
            for n in news:
                send(f"🧠 市場情報:\n{n}")

        except Exception as e:
            send(f"❌ 情報錯誤: {e}")

        time.sleep(900)  # 每15分鐘

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
