import os
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Flask 应用初始化
app = Flask(__name__)

# 读取环境变量（确保在 Render 设置 BOT_TOKEN 和 HELIUS_API_KEY）
BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")
if not HELIUS_API_KEY:
    raise ValueError("请设置环境变量 HELIUS_API_KEY")

# 初始化 Telegram Bot 应用（python-telegram-bot v20+）
application = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

# /start 命令处理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("机器人启动成功！请发送 Solana 合约地址进行分析。")

# 简单示例：收到消息后回复收到的内容
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # 这里你可以加入对合约地址的判断和分析逻辑
    reply_text = f"收到消息：{text}\n这里可以写合约分析逻辑。"
    await update.message.reply_text(reply_text)

# 注册处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# Flask 路由，Telegram Webhook 入口
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            update = Update.de_json(json_data, bot)
            application.update_queue.put(update)
        except Exception as e:
            print(f"Webhook 错误: {e}")
            abort(400)
        return "OK"
    else:
        abort(405)

# 运行 Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)