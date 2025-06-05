import os
import requests
import pandas as pd
import pandas_ta as ta
import numpy as np
from flask import Flask, request

# 设置 NaN 替代
npNaN = np.nan

# 初始化 Flask 应用
app = Flask(name)

# 从环境变量中获取配置
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")

# Telegram API 发送消息
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# 获取 Solana 代币 K 线数据（通过 Helius API）
def fetch_candles(token_address):
    url = f"https://api.helius.xyz/v1/market-data/token/{token_address}/candles?timeframe=1h&api-key={HELIUS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data

# 进行技术指标分析
def analyze_token(token_address):
    try:
        candles = fetch_candles(token_address)
        if not candles or len(candles) < 50:
            return "数据不足，无法分析该代币。"

        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['start'])
        df.set_index('timestamp', inplace=True)
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 计算指标
        rsi = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        ma50 = ta.sma(df['close'], length=50)
        ma200 = ta.sma(df['close'], length=200)
        bb = ta.bbands(df['close'])

        # 当前值
        latest_close = df['close'].iloc[-1]
        latest_rsi = rsi.iloc[-1]
        latest_macd = macd['MACD_12_26_9'].iloc[-1]
        latest_signal = macd['MACDs_12_26_9'].iloc[-1]
        latest_ma50 = ma50.iloc[-1]
        latest_ma200 = ma200.iloc[-1]
        bb_upper = bb['BBU_20_2.0'].iloc[-1]
        bb_lower = bb['BBL_20_2.0'].iloc[-1]

        summary = f"""📊 代币分析结果：
- 当前价格：{latest_close:.6f}
- RSI：{latest_rsi:.2f}（{'超买' if latest_rsi > 70 else '超卖' if latest_rsi < 30 else '中性'}）
- MACD：{latest_macd:.6f}
- Signal：{latest_signal:.6f}
- MA50：{latest_ma50:.6f}
- MA200：{latest_ma200:.6f}
- 布林带上轨：{bb_upper:.6f}
- 布林带下轨：{bb_lower:.6f}
"""
        return summary
    except Exception as e:
        return f"分析出错：{str(e)}"

# 设置 Webhook 路由
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        if text.startswith("http"):
            token_address = text.split("/")[-1]
        else:
            token_address = text.strip()

        result = analyze_token(token_address)
        send_message(chat_id, result)

    return {"ok": True}

# 主页测试用
@app.route("/", methods=["GET"])
def home():
    return "✅ Solana 分析机器人已上线。"

# 启动服务器
if name == "main":
    app.run(host="0.0.0.0", port=10000)