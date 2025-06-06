import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from analysis import analyze_token  # 假设你的分析逻辑在 analysis.py 里
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 指令处理器
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("请发送 Solana 合约地址，我将为你分析代币。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    result = analyze_token(address)
    await update.message.reply_text(result)

# 添加处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask 路由，用于 Render 启动服务
@app.route('/')
def home():
    return "Telegram Solana 分析机器人已上线。"

# 启动 Telegram bot（异步）
@app.before_first_request
def run_telegram_bot():
    import threading
    threading.Thread(target=application.run_polling, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))