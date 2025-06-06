import os
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Flask 应用
app = Flask(__name__)

# 读取环境变量（确保你 Render 环境变量里是 BOT_TOKEN 和 HELIUS_API_KEY）
TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")

# 初始化 Telegram Bot 应用（python-telegram-bot v20+）
application = Application.builder().token(TOKEN).build()
bot = Bot(token=TOKEN)

# 定义 /start 命令的处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("机器人启动成功！发送合约地址即可分析。")

# 给 application 添加命令处理器
application.add_handler(CommandHandler("start", start))

# Flask 路由，用于接收 Telegram Webhook 事件
@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(force=True), bot)
            application.update_queue.put(update)
        except Exception as e:
            print(f"处理更新时出错: {e}")
            abort(400)
        return "OK"
    else:
        abort(405)

if __name__ == "__main__":
    # Flask 默认端口 5000，可以 Render 配置其他端口
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))