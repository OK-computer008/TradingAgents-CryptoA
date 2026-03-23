<div align="center">

# TradingAgents-CryptoA

**Multi-Agent LLM Analysis Framework for A-Shares + Crypto**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

English | [中文](./README_CN.md)

</div>

---

## Overview

TradingAgents-CryptoA is an enhanced fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents), adding support for **Chinese A-share market** and **cryptocurrency** multi-agent analysis.

The framework deploys specialized LLM-powered agents (fundamental analysts, sentiment experts, technical analysts, traders, risk management teams) that collaboratively evaluate market conditions and produce trading decisions.

### Comparison: Original vs CN vs CryptoA

|  | [Original](https://github.com/TauricResearch/TradingAgents) | [CN Version](https://github.com/hsliuping/TradingAgents-CN) | **CryptoA (this project)** |
|---|---|---|---|
| **A-Share** | ❌ | ✅ Tushare / AKShare / BaoStock | ✅ AKShare (free, no registration) |
| **Crypto** | ❌ | ❌ | ✅ CCXT (Binance / OKX / Bybit) |
| **US Stocks** | ✅ yfinance / Alpha Vantage | ✅ | ✅ inherited |
| **On-Chain Agent** | ❌ | ❌ | ✅ whale tracking / open interest |
| **Policy Agent** | ❌ | ❌ | ✅ PBOC / CSRC policy analysis |
| **Fund Flow Agent** | ❌ | ❌ | ✅ northbound / institutional flows |
| **CN Sentiment Agent** | ❌ | ✅ | ✅ Eastmoney / Xueqiu sentiment |
| **News Filter** | ❌ | ✅ multi-layer + quality scoring | ✅ dedup / ad removal / freshness / relevance |
| **LLM Providers** | OpenAI | OpenAI / Gemini / DeepSeek / Qwen | 8 providers (OpenAI / Claude / Gemini / DeepSeek / Qwen / xAI / OpenRouter / Ollama) |
| **WebUI** | ❌ | ✅ Vue 3 + Element Plus | ❌ CLI-first |
| **DB Cache** | ❌ | ✅ MongoDB + Redis | ❌ file-based cache |
| **Docker** | ❌ | ✅ multi-arch | ❌ local execution |
| **License** | Apache 2.0 | Mixed (WebUI requires commercial license) | Apache 2.0 (fully open source) |

### Strengths

- 🔗 **Only TradingAgents fork with cryptocurrency support**
- 🆓 **Zero-cost data** — AKShare + CCXT are free, no paid data subscriptions required
- ⛓ **On-chain analysis** — unique on-chain agent for DeFi / derivatives traders
- 🔌 **Widest LLM compatibility** — 8 providers + local Ollama
- 📜 **Fully open source** — Apache 2.0, no commercial license restrictions

### Current Limitations

- 🖥 No WebUI yet (CLI-first; may be added later)
- 🐳 No Docker deployment yet (planned for a future release)
- 📊 A-share financial data relies on AKShare; fields may be less comprehensive than Tushare
- 🧪 Early stage — agent prompts and workflows are under active optimization

## Quick Start

### Installation

```bash
git clone https://github.com/OK-computer008/TradingAgents-CryptoA.git
cd TradingAgents-CryptoA

# Create virtual environment
conda create -n tradingagents python=3.13
conda activate tradingagents

# Install dependencies
pip install -r requirements.txt
```

### Configure API Keys

Copy the environment template and fill in your API key(s):

```bash
cp .env.example .env
```

You only need to set the key for the LLM provider you plan to use.

### Run A-Share Analysis

```bash
python run_a_share.py
```

Default target: `000060.SZ`. Modify the ticker and date as needed:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import get_a_share_config

config = get_a_share_config()
config["llm_provider"] = "deepseek"
config["deep_think_llm"] = "deepseek-chat"
config["quick_think_llm"] = "deepseek-chat"

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("600519.SH", "2026-03-20")
print(decision)
```

### Run Crypto Analysis

```bash
python run_crypto.py
```

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import get_crypto_config

config = get_crypto_config(exchange="binance")
config["llm_provider"] = "anthropic"
config["deep_think_llm"] = "claude-sonnet-4-5"
config["quick_think_llm"] = "claude-haiku-4-5"

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("BTC/USDT", "2026-03-20")
print(decision)
```

## Supported LLM Providers

| Provider | Env Variable | Example Models |
|----------|-------------|----------------|
| OpenAI | `OPENAI_API_KEY` | gpt-5.2, gpt-5-mini, gpt-4.1 |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4-5, claude-haiku-4-5 |
| Google | `GOOGLE_API_KEY` | gemini-2.5-pro, gemini-2.5-flash |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat, deepseek-reasoner |
| DashScope (Qwen) | `DASHSCOPE_API_KEY` | qwen-max, qwen-plus, qwen-turbo |
| xAI | `XAI_API_KEY` | grok-4-0709 |
| OpenRouter | `OPENROUTER_API_KEY` | Any OpenRouter-supported model |
| Ollama (local) | None required | Any locally deployed model |

## Analyst Combinations

### A-Share Mode
market + fundamentals + cn_sentiment + policy + fund_flow + news

### Crypto Mode
market + onchain + news

### US Stock Mode (upstream default)
fundamentals + sentiment + news + technical

## Project Structure

```
tradingagents/
  agents/          # Multi-agent definitions (analysts, researchers, trader, risk)
  dataflows/       # Data source adapters (AKShare, CCXT, yfinance)
  graph/           # LangGraph workflow orchestration
  llm_clients/     # Multi-LLM client factory
  default_config.py
run_a_share.py     # A-share analysis example
run_crypto.py      # Crypto analysis example
```

## Acknowledgments

This project is built on [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents). We thank the original authors for their open-source contribution.

**Original paper citation:**

```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework},
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138},
}
```

## Disclaimer

**This project is for educational and research purposes only. It does not constitute investment advice.**

- Trading decisions are influenced by many factors including LLM model choice, data quality, and market conditions
- The project maintainers bear no responsibility for any losses incurred from live trading using this framework
- Please use this project with full awareness of the risks involved
- A-share and cryptocurrency markets carry significant risk — comply with local laws and regulations

## License

Apache 2.0
