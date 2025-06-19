import aiohttp
import pandas as pd
import ta

async def analyze_rsi_macd_for_token(token_address: str) -> str:
    url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{token_address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
        candles = data.get("pair", {}).get("candles", [])
        if len(candles) < 20:
            return "❌ K线数据不足，可能无效地址。"

        df = pd.DataFrame(candles)
        df['close'] = df['close'].astype(float)
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        last = df.iloc[-1]
        rsi = last['rsi']
        diff = last['macd'] - last['macd_signal']
        macd_signal = "金叉" if diff > 0 else "死叉"
        advise = "观望"
        if rsi < 30 and diff > 0:
            advise = "✅ 建议买入"
        elif rsi > 70 and diff < 0:
            advise = "❌ 建议卖出"

        return f"📊 分析结果（{token_address}）\nRSI: {rsi:.2f}\nMACD: {macd_signal}\n➤ {advise}"
    except Exception as e:
        return f"❌ 分析失败：{e}"