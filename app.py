from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters
import pandas as pd
import pandas_ta as ta
import requests
import logging

# 启动 Flask 应用
app = Flask(__name__)

# 直接写入你的 Telegram 机器人 Token（调试用，部署后建议改回 os.getenv）
TOKEN = "8151561242:AAGMbaA1TDBH1Ohb2gotSVy-mpEzERc2Av4"
bot = Bot(token=TOKEN)

# 初始化 Dispatcher
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Helius API 配置（推荐仍用环境变量，便于私密保存）
import os
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

# 获取 Solana 代币 K 线数据
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

# 分析函数
def analyze_token(token_address):
    df = fetch_candlestick_data(token_address)
    if df is None or df.empty:
        return "❌ 无法获取 K 线数据，请检查合约地址是否正确。"

    df['rsi'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    df['macd'] = macd['MACD_12_26_9']
    df['signal'] = macd['MACDs_12_26_9']
    df['hist'] = macd['MACDh_12_26_9']

    last = df.iloc[-1]
    summary = (
        f"📊 分析结果:\n"
        f"RSI: {last['rsi']:.2f}\n"
        f"MACD: {last['macd']:.4f}\n"
        f"Signal: {last['signal']:.4f}\n"
        f"Histogram: {last['hist']:.4f}\n"
    )
    return summary

# 处理消息
def handle_message(update: Update, context):
    token_address = update.message.text.strip()
    result = analyze_token(token_address)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

# /start 命令
def start(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="欢迎使用 Solana 分析机器人，请发送代币合约地址进行分析。")

# 添加处理器
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook 路由
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# 首页路由
@app.route("/", methods=["GET"])
def index():
    return "✅ Solana 分析机器人正在运行..."

# 启动入口
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)