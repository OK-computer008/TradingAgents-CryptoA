"""
TradingAgents A股分析示例 — 使用 AKShare 数据源 + 中国化 Agent
"""
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG, get_a_share_config

from dotenv import load_dotenv
load_dotenv()

# ===== 使用A股预设配置 =====
config = get_a_share_config()

# LLM 配置 — 按需修改
# 支持的 llm_provider: openai, anthropic, google, deepseek, dashscope, ollama, openrouter, xai
config["llm_provider"] = "anthropic"
config["backend_url"] = "http://127.0.0.1:15721"      # 本地代理（如不需要可删除此行）
config["deep_think_llm"] = "claude-sonnet-4-5"          # 深度思考模型
config["quick_think_llm"] = "claude-haiku-4-5"          # 快速任务模型

# 辩论轮数
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

# ===== 初始化并运行 =====
# A股模式自动选择分析师组合：
# market + fundamentals + cn_sentiment + policy + fund_flow + news
ta = TradingAgentsGraph(debug=True, config=config)

# 分析目标：中金岭南 (000060.SZ)
_, decision = ta.propagate("000060.SZ", "2025-03-20")
print("\n" + "=" * 60)
print("最终交易决策:")
print("=" * 60)
print(decision)
