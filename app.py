import os
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from utils.analysis import analyze_rsi_macd_for_token

# Flask Web 服务器
app = Flask(__name__)

# 从环境变量中读取配置
BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN:
    raise ValueError("请设置 BOT_TOKEN")
if not HELIUS_API_KEY:
    raise ValueError("请设置 HELIUS_API_KEY")

# 初始化 Telegram 应用
application = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

# 启动命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 机器人已启动，请发送 Solana 合约地址进行分析。")

# 地址处理逻辑
async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    await update.message.reply_text("🔍 正在分析，请稍候...")
    try:
        result = await analyze_rsi_macd_for_token(address)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 分析出错：{e}")

# 注册 Handler
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_address))

# 设置 Webhook 接收器
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)
        # 修复：使用 .process_update 调度异步处理器
        application.create_task(application.process_update(update))
        return "OK"
    else:
        abort(405)

# 启动 Flask App
if __name__ == "__main__":
    import asyncio
    async def main():
        await application.initialize()
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)

    asyncio.run(main())