import os
import asyncio
import logging
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from utils.analysis import analyze_rsi_macd_for_token

# 配置日志，方便排查
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")
if not HELIUS_API_KEY:
    raise ValueError("请设置环境变量 HELIUS_API_KEY")

application = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

# /start 命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"收到 /start 命令，来自用户：{update.effective_user.id}")
    await update.message.reply_text("🤖 机器人已启动，请发送 Solana 合约地址进行分析。")

# 处理用户发送的合约地址文本
async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    logger.info(f"收到合约地址消息：{address}，用户：{update.effective_user.id}")
    await update.message.reply_text("🔍 正在分析，请稍候...")
    try:
        result = await analyze_rsi_macd_for_token(address)
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(f"分析错误: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 分析出错：{e}")

# 注册命令和消息处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_address))

# Flask 接收 Telegram Webhook 请求
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, bot)
            # 异步执行 update 处理
            asyncio.run(application.process_update(update))
        except Exception as e:
            logger.error(f"Webhook 处理错误: {e}", exc_info=True)
            abort(400)
        return "OK"
    else:
        abort(405)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"启动 Flask 服务，监听端口 {port}")
    app.run(host="0.0.0.0", port=port)