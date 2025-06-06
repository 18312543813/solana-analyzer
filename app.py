import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

if not BOT_TOKEN or not HELIUS_API_KEY:
    raise Exception("请在环境变量中设置 BOT_TOKEN 和 HELIUS_API_KEY")

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def start(update: Update, context):
    update.message.reply_text(
        "欢迎！发送 Solana 代币合约地址，我帮你查询实时行情。"
    )

def fetch_solana_token_price(contract_address: str):
    # 调用 Helius API 获取最新价格
    # 注意：Helius 本身不直接提供价格接口，这里示例用 Solana RPC + 一些公共接口
    # 你需要替换成你有的接口或自己搭价格数据，下面仅做示范
    url = f"https://api.helius.xyz/v0/tokens/metadata?api-key={HELIUS_API_KEY}"
    # 实际调用请改成真实价格接口，这里示例简单查询元数据
    params = {"mint": contract_address}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data and "metadata" in data:
            meta = data["metadata"][0]
            name = meta.get("name", "未知")
            symbol = meta.get("symbol", "未知")
            return f"代币名称：{name}\n代币符号：{symbol}\n（这里只是示范，需接真实行情接口）"
        else:
            return "未找到该代币的元数据，请确认合约地址正确。"
    except Exception as e:
        return f"查询失败: {e}"

def handle_message(update: Update, context):
    text = update.message.text.strip()
    # 简单判断是否可能是合约地址（长度44左右）
    if len(text) == 44:
        reply = fetch_solana_token_price(text)
    else:
        reply = "请发送有效的 Solana 代币合约地址（44字符左右）"
    update.message.reply_text(reply)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/")
def index():
    return "机器人运行正常..."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)