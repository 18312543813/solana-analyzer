import os
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask, request

app = Flask(name)

# Helius API Key，建议用环境变量，这里默认写你的Key
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "28e1ff17-e745-4065-bf76-bb51c4e76ed9")

# Telegram Bot Token，建议用环境变量，这里默认写你的Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7812463122:AAH4jp78hloiwpIbO8Uq4w2n-mtzcJtROCI")

# 获取真实1小时K线数据函数
def fetch_ohlcv(token_address):
    url = f"https://api.helius.xyz/v0/tokens/{token_address}/price?api-key={HELIUS_API_KEY}&time-series=1h"
    try:
        response = requests.get(url)
        data = response.json()
        ohlcv = pd.DataFrame(data["prices"])
        ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"], unit="s")
        return ohlcv
    except Exception as e:
        print("获取K线数据失败：", e)
        return None

# 简单RSI分析函数
def analyze_token(token_address):
    df = fetch_ohlcv(token_address)
    if df is None or df.empty:
        return "获取数据失败或数据为空"
    df.set_index("timestamp", inplace=True)
    df.ta.rsi(close='close', length=14, append=True)
    last_rsi = df.iloc[-1]['RSI_14']
    signal = "中性"
    if last_rsi > 70:
        signal = "超买，可能下跌"
    elif last_rsi < 30:
        signal = "超卖，可能上涨"
    return f"当前RSI: {last_rsi:.2f}\n分析信号: {signal}"

# 发送消息到Telegram
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# Telegram webhook 接口
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        token_address = data["message"]["text"].strip()
        result = analyze_token(token_address)
        send_message(chat_id, result)
    return "ok"

if name == "main":
    app.run(debug=True)