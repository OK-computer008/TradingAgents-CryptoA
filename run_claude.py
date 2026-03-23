from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create a custom config using Anthropic Claude
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "anthropic"
config["backend_url"] = "http://127.0.0.1:15721"    # 本地中转代理
config["deep_think_llm"] = "claude-sonnet-4-5"       # 深度思考用 Sonnet 4.5
config["quick_think_llm"] = "claude-haiku-4-5"       # 快速任务用 Haiku 4.5
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

# Data vendors - use yfinance (no API key needed)
config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance",
}

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# Analyze 中金岭南 (000060.SZ)
_, decision = ta.propagate("000060.SZ", "2025-03-20")
print(decision)
