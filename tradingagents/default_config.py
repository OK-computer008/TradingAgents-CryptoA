import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    # Supported providers: openai, anthropic, google, deepseek, dashscope, ollama, openrouter, xai
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.2",
    "quick_think_llm": "gpt-5-mini",
    "backend_url": "https://api.openai.com/v1",
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # ===== Market type configuration =====
    # "us_stock" - US stocks (default, uses yfinance/alpha_vantage)
    # "a_share"  - Chinese A-shares (uses akshare)
    # "crypto"   - Cryptocurrency (uses ccxt)
    "market_type": "us_stock",
    # Output language: "en" for English, "zh" for Chinese
    "output_language": "en",
    # Crypto-specific settings
    "crypto_exchange": "binance",  # CCXT exchange id: binance, okx, bybit, etc.
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: alpha_vantage, yfinance, akshare, ccxt
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance, akshare, ccxt
        "fundamental_data": "yfinance",      # Options: alpha_vantage, yfinance, akshare, ccxt
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance, akshare
        "cn_market_data": "akshare",         # Options: akshare (A-share specific)
        "cn_policy_data": "akshare",         # Options: akshare
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
}


# ===== Preset configurations for different markets =====

def get_a_share_config(base_config=None):
    """Get preset configuration for A-share (Chinese stock market)."""
    config = (base_config or DEFAULT_CONFIG).copy()
    config["market_type"] = "a_share"
    config["output_language"] = "zh"
    config["data_vendors"] = {
        "core_stock_apis": "akshare",
        "technical_indicators": "akshare",
        "fundamental_data": "akshare",
        "news_data": "akshare",
        "cn_market_data": "akshare",
        "cn_policy_data": "akshare",
    }
    return config


def get_crypto_config(base_config=None, exchange="binance"):
    """Get preset configuration for cryptocurrency."""
    config = (base_config or DEFAULT_CONFIG).copy()
    config["market_type"] = "crypto"
    config["output_language"] = "en"
    config["crypto_exchange"] = exchange
    config["data_vendors"] = {
        "core_stock_apis": "ccxt",
        "technical_indicators": "ccxt",
        "fundamental_data": "ccxt",
        "news_data": "yfinance",  # Fallback to yfinance for news
        "cn_market_data": "akshare",
        "cn_policy_data": "akshare",
    }
    return config
