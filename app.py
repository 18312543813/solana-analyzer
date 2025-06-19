import os
import asyncio
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.analysis import analyze_rsi_macd_for_token  # 你的分析函数

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# 创建新的事件循环给 Application 用
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(application.initialize())

# 注册命令和消息处理器
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
    if request.method == "POST":
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)

        # 在线程中安全地提交异步任务给事件循环
        future = asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
        try:
            future.result(timeout=10)  # 等待最多10秒
        except Exception as e:
            print(f"Webhook 处理异常: {e}")
            abort(500)
        return "OK"
    else:
        abort(405)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)