"""
TradingAgents 加密货币分析示例 — 使用 CCXT 数据源
"""
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import get_crypto_config

from dotenv import load_dotenv
load_dotenv()

# ===== 使用加密货币预设配置 =====
config = get_crypto_config(exchange="binance")

# LLM 配置 — 按需修改
# Supported llm_provider: openai, anthropic, google, deepseek, dashscope, ollama, openrouter, xai
config["llm_provider"] = "anthropic"
# config["backend_url"] = "http://127.0.0.1:15721"      # 本地代理（如不需要可删除此行）
config["deep_think_llm"] = "claude-sonnet-4-5"
config["quick_think_llm"] = "claude-haiku-4-5"

# 辩论轮数
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

# ===== 初始化并运行 =====
# 加密货币模式自动选择分析师组合：
# market + onchain + news
ta = TradingAgentsGraph(debug=True, config=config)

# 分析目标：BTC/USDT
_, decision = ta.propagate("BTC/USDT", "2025-03-20")
print("\n" + "=" * 60)
print("Final Trading Decision:")
print("=" * 60)
print(decision)
