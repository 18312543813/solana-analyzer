import os
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.analysis import analyze_rsi_macd_for_token

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("请设置 BOT_TOKEN")

async def start(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot 启动！发地址试试。")

async def handle_address(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 分析中...")
    address = update.message.text.strip()
    result = await analyze_rsi_macd_for_token(address)
    await update.message.reply_text(result)

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address))

if __name__ == "__main__":
    print("启动 Bot 轮询模式")
    app.run_polling()