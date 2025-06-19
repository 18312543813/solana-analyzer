# app.py

import os
import asyncio
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.analysis import analyze_rsi_macd_for_token

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# 用独立线程中的事件循环保持 webhook 持久不挂
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(application.initialize())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 发送 Solana 合约地址，我将分析 RSI + MACD。")

async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    await update.message.reply_text("⏳ 正在分析，请稍候...")
    result = await analyze_rsi_macd_for_token(address)
    await update.message.reply_text(result)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        future = asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
        future.result(timeout=15)
        return "OK"
    except Exception as e:
        print(f"Webhook处理异常：{e}")
        abort(500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)