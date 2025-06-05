import os
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask, request
from telegram import Bot

# 配置环境变量（Render 中设置）
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY")

app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)


def fetch_kline_data(mint_address):
    url = f"https://api.helius.xyz/v0/tokens/{mint_address}/price?api-key={HELIUS_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()
    # 假设返回的是历史价格列表
    prices = data.get("prices", [])
    if not prices:
        return None

    df = pd.DataFrame(prices)
    df['close'] = df['price']
    df['time'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('time', inplace=True)
    return df


def analyze(df):
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['macd'] = ta.macd(df['close'])['MACD_12_26_9']
    df['kdj'] = ta.stoch(df['close'])
    df['ma20'] = ta.sma(df['close'], length=20)
    df['boll_upper'] = ta.bbands(df['close'])['BBU_20_2.0']
    df['boll_lower'] = ta.bbands(df['close'])['BBL_20_2.0']

    latest = df.iloc[-1]
    return {
        'RSI': round(latest['rsi'], 2),
        'MACD': round(latest['macd'], 6),
        'K': round(latest['kdj']['STOCHk_14_3_3'], 2),
        'D': round(latest['kdj']['STOCHd_14_3_3'], 2),
        'MA20': round(latest['ma20'], 6),
        'BOLL上轨': round(latest['boll_upper'], 6),
        'BOLL下轨': round(latest['boll_lower'], 6)
    }


@app.route('/', methods=['GET'])
def home():
    return "Solana Analyzer Bot is running."


@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" not in update:
        return "ok"

    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text.startswith("So111") or len(text) > 20:
        df = fetch_kline_data(text)
        if df is None:
            bot.send_message(chat_id=chat_id, text="❌ 获取数据失败，检查合约地址或稍后重试。")
            return "ok"

        result = analyze(df)
        reply = "\n".join(f"{k}: {v}" for k, v in result.items())
        bot.send_message(chat_id=chat_id, text=f"✅ 分析结果：\n{reply}")
    else:
        bot.send_message(chat_id=chat_id, text="请发送 Solana 合约地址进行分析。")

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
