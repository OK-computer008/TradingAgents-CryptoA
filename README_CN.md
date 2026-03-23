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

### 三个版本横向对比

|  | [原版](https://github.com/TauricResearch/TradingAgents) | [CN 中文增强版](https://github.com/hsliuping/TradingAgents-CN) | **本项目 (CryptoA)** |
|---|---|---|---|
| **A股支持** | ❌ | ✅ Tushare / AKShare / BaoStock | ✅ AKShare（免费，零注册） |
| **加密货币** | ❌ | ❌ | ✅ CCXT（Binance / OKX / Bybit） |
| **美股支持** | ✅ yfinance / Alpha Vantage | ✅ | ✅ 继承原版 |
| **链上分析 Agent** | ❌ | ❌ | ✅ 巨鲸追踪 / 合约持仓 |
| **政策分析 Agent** | ❌ | ❌ | ✅ 央行 / 证监会政策解读 |
| **资金流 Agent** | ❌ | ❌ | ✅ 北向资金 / 主力资金 |
| **中文情绪 Agent** | ❌ | ✅ | ✅ 股吧 / 雪球情绪 |
| **新闻过滤** | ❌ | ✅ 多层过滤 + 质量评估 | ✅ 去重 / 去广告 / 时效性 / 相关性 |
| **LLM 供应商** | OpenAI | OpenAI / Gemini / DeepSeek / 通义千问 | 8 种（OpenAI / Claude / Gemini / DeepSeek / 通义千问 / xAI / OpenRouter / Ollama） |
| **WebUI** | ❌ | ✅ Vue 3 + Element Plus | ❌ CLI 优先 |
| **数据库缓存** | ❌ | ✅ MongoDB + Redis | ❌ 文件缓存 |
| **Docker 部署** | ❌ | ✅ 多架构 | ❌ 本地运行 |
| **License** | Apache 2.0 | 混合授权（WebUI 需商业授权） | Apache 2.0（完全开源） |

### 我们的优势

- 🔗 **唯一支持加密货币**的 TradingAgents 衍生版本
- 🆓 **零成本数据源** — AKShare + CCXT 全免费，无需注册付费数据服务
- ⛓ **链上分析能力** — 独有的链上分析 Agent，适合 DeFi / 合约交易者
- 🔌 **最广泛的 LLM 兼容** — 8 种供应商 + Ollama 本地部署
- 📜 **完全开源** — Apache 2.0，无商业授权限制

### 当前局限

- 🖥 暂无 WebUI（CLI 优先，后续可能添加）
- 🐳 暂无 Docker 部署（后续版本计划支持）
- 📊 A股财报数据依赖 AKShare，字段可能不如 Tushare 丰富
- 🧪 项目处于早期阶段，Agent prompt 和工作流仍在持续优化

## 快速开始

### 安装

```bash
git clone https://github.com/Sliminem0410/TradingAgents-CryptoA.git
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
