import os
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# 初始化 Flask 应用
app = Flask(__name__)

# 环境变量读取
BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")
if not HELIUS_API_KEY:
    raise ValueError("请设置环境变量 HELIUS_API_KEY")

# 初始化 Telegram Bot
application = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

# 处理 /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 机器人已启动，请发送 Solana 合约地址进行分析。")

# 处理文本消息
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    reply_text = f"收到消息：{text}\n（此处可以写合约分析逻辑）"
    await update.message.reply_text(reply_text)

# 注册处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# 设置 Webhook 的 Flask 路由
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            print("✅ 收到 Webhook 数据：", json_data)
            update = Update.de_json(json_data, bot)
            application.update_queue.put(update)
        except Exception as e:
            print(f"❌ Webhook 错误: {e}")
            abort(400)
        return "OK"
    else:
        abort(405)

# ❗不要使用 app.run()，Render 将通过 gunicorn 启动