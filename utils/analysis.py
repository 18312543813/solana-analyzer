import aiohttp
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

# 时间周期与 bar size 映射（单位分钟）
INTERVALS = {
    '1m': 1,
    '5m': 5,
    '1h': 60,
    '4h': 240
}

async def fetch_ohlcv(token_address: str, interval: str = '5m', limit: int = 100):
    url = f"https://api.helius.xyz/v0/token-metadata/{token_address}/candles?api-key={HELIUS_API_KEY}&bar={interval}&limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"获取 K 线失败: {resp.status}")
            data = await resp.json()
            return pd.DataFrame(data['candles'])

# RSI 计算
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 简化 MACD 计算
def calculate_macd(prices):
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

async def analyze_rsi_macd_for_token(address: str):
    messages = [f"📊 合约地址：{address}\n"]
    for label, minutes in INTERVALS.items():
        try:
            df = await fetch_ohlcv(address, interval=label, limit=100)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            prices = df['close']

            rsi = calculate_rsi(prices).iloc[-1]
            macd, signal = calculate_macd(prices)
            macd_val = macd.iloc[-1]
            signal_val = signal.iloc[-1]
            trend = "🔼 金叉" if macd_val > signal_val else "🔽 死叉"

            if rsi < 30:
                suggestion = "🟢 超卖，可能反弹"
            elif rsi > 70:
                suggestion = "🔴 超买，注意风险"
            else:
                suggestion = "🟡 中性，继续观察"

            messages.append(f"⏱️ {label} RSI: {rsi:.2f} | {suggestion} | {trend}")
        except Exception as e:
            messages.append(f"❌ {label} 分析失败：{e}")

    return "\n".join(messages)