import os
import asyncio
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# 初始化 Flask 应用
app = Flask(__name__)

# 读取环境变量
BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN:
    raise ValueError("请设置环境变量 BOT_TOKEN")
if not HELIUS_API_KEY:
    raise ValueError("请设置环境变量 HELIUS_API_KEY")

# ✅ 创建 Telegram Bot 应用（连接池优化）
application: Application = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .concurrent_updates(True)
    .get_updates_pool_timeout(10)
    .build()
)

# /start 命令处理器
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📥 收到 /start 命令")
    await update.message.reply_text("🤖 机器人已启动，请发送 Solana 合约地址进行分析。")

# 文本消息处理器（合约地址）
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        print("📥 收到普通消息：", text)
        reply_text = f"收到消息：{text}\n（此处可以写合约分析逻辑）"
        await update.message.reply_text(reply_text)
    except Exception as e:
        print(f"❌ echo 处理出错: {e}")

# ✅ 注册指令与文本处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

# Webhook 路由
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            print("✅ 收到 Webhook 数据：", json_data)

            update = Update.de_json(json_data, application.bot)

            async def process():
                try:
                    if not application._initialized:
                        print("🌀 初始化 application...")
                        await application.initialize()
                    await application.process_update(update)
                except Exception as e:
                    print(f"❌ 消息处理出错: {e}")

            # 使用事件循环处理，不关闭，防止 loop 已关闭错误
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process())

        except Exception as e:
            print(f"❌ Webhook 错误: {e}")
            abort(400)
        return "OK"
    else:
        abort(405)