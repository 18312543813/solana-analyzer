from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import pandas as pd
import pandas_ta as ta
import requests
import logging
import os

# 启动 Flask 应用
app = Flask(__name__)

# Telegram 机器人密钥
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

# 初始化调度器
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Helius API 配置
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

def fetch_candlestick_data(token_address):
    url = f"https://api.helius.xyz/v1/token/{token_address}/candlesticks?api-key={HELIUS_API_KEY}&timeframe=5m&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['startTime'])
        df.set_index('time', inplace=True)
        return df
    else:
        return None

def analyze_token(token_address):
    df = fetch_candlestick_data(token_address)
    if df is None or df.empty:
        return "无法获取 K 线数据，请检查合约地址是否正确。"

    df['rsi'] = ta.rsi(df['close'], length=14)
    df['macd'] = ta.macd(df['close'])['MACD_12_26_9']
    df['signal'] = ta.macd(df['close'])['MACDs_12_26_9']
    df['hist'] = ta.macd(df['close'])['MACDh_12_26_9']

    last = df.iloc[-1]
    summary = (
        f"📊 分析结果:\n"
        f"RSI: {last['rsi']:.2f}\n"
        f"MACD: {last['macd']:.4f}\n"
        f"Signal: {last['signal']:.4f}\n"
        f"Histogram: {last['hist']:.4f}\n"
    )
    return summary

def handle_message(update: Update, context):
    token_address = update.message.text.strip()
    result = analyze_token(token_address)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def start(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="欢迎使用 Solana 分析机器人，请发送代币合约地址进行分析。")

# 添加处理器
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask 路由
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Solana 分析机器人运行中"

# 启动入口
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
