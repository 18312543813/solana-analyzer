from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import pandas as pd
import pandas_ta as ta
import requests
import os

app = Flask(__name__)

# 获取环境变量
TOKEN = os.getenv("TELEGRAM_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

# 分析代币函数
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
        f"Histogram: {last['hist']:.4f}"
    )
    return summary

# Telegram 命令处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 Solana 分析机器人，请发送代币合约地址进行分析。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token_address = update.message.text.strip()
    result = analyze_token(token_address)
    await update.message.reply_text(result)

# 启动机器人
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 设置 Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "✅ Solana 分析机器人运行中"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)