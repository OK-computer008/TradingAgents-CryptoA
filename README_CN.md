<div align="center">

# TradingAgents-CryptoA

**基于 TradingAgents 的 A股 + 加密货币多智能体 LLM 分析框架**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[English](./README.md) | 中文

</div>

---

## 简介

TradingAgents-CryptoA 是在 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 基础上的增强版本，专注于 **A股市场** 和 **加密货币** 的多智能体分析。

框架通过部署多个专业化的 LLM Agent（基本面分析师、情绪分析师、技术分析师、交易员、风控团队等），协同评估市场状况并输出交易决策。

### 相比原版的增强功能

- **A股市场支持** — 基于 AKShare 的 A股行情、财务、资金流数据
- **加密货币支持** — 基于 CCXT 的多交易所加密货币数据（Binance、OKX、Bybit 等）
- **中国化 Agent** — 中文情绪分析师、政策分析师、资金流分析师、链上分析师
- **多 LLM 供应商** — 支持 8 种 LLM 供应商，灵活切换
- **新闻质量过滤** — 去重、去广告、时效性检查、相关性排序
- **中文输出** — A股模式默认中文分析报告

## 快速开始

### 安装

```bash
git clone https://github.com/your-username/TradingAgents-CryptoA.git
cd TradingAgents-CryptoA

# 创建虚拟环境
conda create -n tradingagents python=3.13
conda activate tradingagents

# 安装依赖
pip install -r requirements.txt
```

### 配置 API Key

复制环境变量模板并填入你的 API Key：

```bash
cp .env.example .env
```

只需配置你实际使用的 LLM 供应商对应的 Key 即可。

### 运行 A股分析

```bash
python run_a_share.py
```

`run_a_share.py` 默认分析 `000060.SZ`（中金岭南），你可以修改 ticker 和日期：

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import get_a_share_config

config = get_a_share_config()
config["llm_provider"] = "deepseek"           # 选择你的 LLM 供应商
config["deep_think_llm"] = "deepseek-chat"
config["quick_think_llm"] = "deepseek-chat"

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("600519.SH", "2026-03-20")
print(decision)
```

### 运行加密货币分析

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

## 支持的 LLM 供应商

| 供应商 | 环境变量 | 示例模型 |
|--------|----------|----------|
| OpenAI | `OPENAI_API_KEY` | gpt-5.2, gpt-5-mini, gpt-4.1 |
| Anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4-5, claude-haiku-4-5 |
| Google | `GOOGLE_API_KEY` | gemini-2.5-pro, gemini-2.5-flash |
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat, deepseek-reasoner |
| 通义千问 (DashScope) | `DASHSCOPE_API_KEY` | qwen-max, qwen-plus, qwen-turbo |
| xAI | `XAI_API_KEY` | grok-4-0709 |
| OpenRouter | `OPENROUTER_API_KEY` | 任意 OpenRouter 支持的模型 |
| Ollama (本地) | 无需 Key | 本地部署的任意模型 |

## 分析师组合

### A股模式
market + fundamentals + cn_sentiment + policy + fund_flow + news

### 加密货币模式
market + onchain + news

### 美股模式（原版）
fundamentals + sentiment + news + technical

## 项目结构

```
tradingagents/
  agents/          # 多智能体定义（分析师、研究员、交易员、风控）
  dataflows/       # 数据源适配（AKShare, CCXT, yfinance）
  graph/           # LangGraph 工作流编排
  llm_clients/     # 多 LLM 客户端工厂
  default_config.py
run_a_share.py     # A股分析示例
run_crypto.py      # 加密货币分析示例
```

## 致谢

本项目基于 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) 开发。感谢原作者的开源贡献。

**原论文引用：**

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

## 免责声明

**本项目仅用于学习研究目的，不构成任何投资建议。**

- 交易决策受多种因素影响，包括 LLM 模型选择、数据质量、市场环境等
- 使用本框架进行实盘交易所产生的任何损失，项目维护者不承担任何责任
- 请在充分了解风险的前提下使用本项目
- 中国 A股、加密货币等市场均存在较高风险，请遵守当地法律法规

## License

Apache 2.0
