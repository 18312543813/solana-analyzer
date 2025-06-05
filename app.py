import os
import requests
import pandas as pd
import pandas_ta as ta
import numpy as np
from flask import Flask, request

# 修复 pandas_ta 中 NaN 引用错误
ta.npNaN = np.nan

app = Flask(name)

HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def fetch_kline_data(token_address):
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    headers = {"Content-Type": "application/json"}

    data = {
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "getAssetPriceChart",
        "params": {
            "id": token_address,
            "type": "price",
            "timeFrame": "1H",
        },
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        kline_data = response.json()["result"]["items"]
        df = pd.DataFrame(kline_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        df.rename(columns={"price": "close"}, inplace=True)
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        return None

def analyze_token(df):
    result = []

    # 1. 均线分析
    df["ma7"] = ta.sma(df["close"], length=7)
    df["ma25"] = ta.sma(df["close"], length=25)
    if df["ma7"].iloc[-1] > df["ma25"].iloc[-1]:
        result.append("✅ 短期均线突破长期均线，可能有上涨趋势。")
    else:
        result.append("⚠️ 短期均线未突破长期均线，暂不明朗。")

    # 2. MACD
    macd = ta.macd(df["close"])
    if macd["MACDh_12_26_9"].iloc[-1] > 0:
        result.append("✅ MACD 柱状图为正，可能处于上涨阶段。")
    else:
        result.append("⚠️ MACD 柱状图为负，可能下跌或盘整中。")

    # 3. RSI
    rsi = ta.rsi(df["close"], length=14)
    if rsi.iloc[-1] < 30:
        result.append("🟢 RSI < 30，可能超卖，注意反弹机会。")
    elif rsi.iloc[-1] > 70:
        result.append("🔴 RSI > 70，可能超买，注意风险。")
    else:
        result.append("ℹ️ RSI 正常。")

    return "\n".join(result)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@app.route("/", methods=["GET"])
def home():
    return "Solana Token Analyzer Bot is running."

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip()

        if text.startswith("So111") or text.startswith("7") or len(text) > 30:
            df = fetch_kline_data(text)
            if df is None or df.empty:
                send_message(chat_id, "❌ 获取数据失败，请检查合约地址是否正确。")
            else:
                analysis = analyze_token(df)
                send_message(chat_id, f"📊 分析结果：\n\n{analysis}")
        else:
            send_message(chat_id, "请输入有效的 Solana 合约地址。")
    return "", 200

if name == "main":
    app.run(host="0.0.0.0", port=10000)