import httpx
import pandas as pd
import ta

import os

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
SOLANA_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

async def analyze_rsi_macd_for_token(token_address: str) -> str:
    try:
        timeframes = {
            "1分钟": 1,
            "5分钟": 5,
            "1小时": 60,
            "4小时": 240,
            "1天": 1440,
        }

        result_lines = [f"📊 分析结果 ({token_address}):\n"]

        async with httpx.AsyncClient() as client:
            for name, minutes in timeframes.items():
                url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{token_address}"
                r = await client.get(url)
                data = r.json()

                candles = data.get("pair", {}).get("candles")
                if not candles:
                    result_lines.append(f"{name}: 获取K线失败")
                    continue

                df = pd.DataFrame(candles)[-100:]
                df["close"] = pd.to_numeric(df["close"])

                # 计算 RSI 和 MACD
                df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
                macd = ta.trend.MACD(df["close"])
                df["macd"] = macd.macd()
                df["macd_signal"] = macd.macd_signal()

                rsi_value = df["rsi"].iloc[-1]
                macd_val = df["macd"].iloc[-1]
                macd_sig = df["macd_signal"].iloc[-1]

                # 分析逻辑
                advice = "📌 观望"
                if rsi_value < 30 and macd_val > macd_sig:
                    advice = "✅ 建议买入"
                elif rsi_value > 70 and macd_val < macd_sig:
                    advice = "❌ 建议卖出"

                result_lines.append(f"{name}:\n  RSI: {rsi_value:.2f}\n  MACD: {macd_val:.4f} / Signal: {macd_sig:.4f}\n  ➤ {advice}")

        return "\n\n".join(result_lines)
    except Exception as e:
        return f"❌ 分析失败：{e}"