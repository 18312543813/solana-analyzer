import os
import asyncio
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from utils.analysis import analyze_rsi_macd_for_token

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")
if not HELIUS_API_KEY:
    raise ValueError("请设置环境变量 HELIUS_API_KEY")

application = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 机器人已启动，请发送 Solana 合约地址进行分析。")

async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    await update.message.reply_text("🔍 正在分析，请稍候...")
    try:
        result = await analyze_rsi_macd_for_token(address)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 分析出错：{e}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_address))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)
        # 这里用 asyncio.run 来运行异步代码，解决没有事件循环的错误
        asyncio.run(application.process_update(update))
        return "OK"
    except Exception as e:
        print(f"Webhook 错误: {e}")
        abort(400)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)