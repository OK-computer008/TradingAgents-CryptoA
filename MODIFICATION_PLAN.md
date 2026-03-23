# TradingAgents A股+加密货币 魔改方案

## 改造目标
将 TradingAgents 从美股专用框架改造为支持 **A股 + 加密货币** 的多市场交易分析系统。

---

## Phase 1: 数据层改造（最高优先级）

### 1.1 新增 AKShare 数据源（A股）
**新建文件**: `tradingagents/dataflows/akshare_provider.py`
- 实现函数：get_stock, get_indicator, get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement, get_news, get_global_news
- 数据源：AKShare（免费、无需API Key、A股覆盖全面）
- 技术指标：复用 stockstats 计算

### 1.2 新增 CCXT 数据源（加密货币）
**新建文件**: `tradingagents/dataflows/ccxt_provider.py`
- 实现函数：get_stock（K线数据）, get_indicator（技术指标）
- 支持交易所：Binance, OKX, Bybit 等主流交易所
- 注意：加密货币没有传统基本面数据，需特殊处理

### 1.3 新增中文新闻数据源
**新建文件**: `tradingagents/dataflows/cn_news_provider.py`
- 财经新闻：东方财富、新浪财经
- A股公告：巨潮资讯
- 加密新闻：可选

### 1.4 注册新数据源
**修改文件**: `tradingagents/dataflows/interface.py`
- 在 VENDOR_LIST 中添加 "akshare", "ccxt", "cn_news"
- 在 VENDOR_METHODS 中注册所有新函数

### 1.5 更新配置
**修改文件**: `tradingagents/default_config.py`
- 新增 market_type 配置（"a_share" | "crypto" | "us_stock"）
- 新增 exchange 配置（加密货币交易所选择）

---

## Phase 2: 新增 Agent（中国市场特色）

### 2.1 中文情绪分析师 (CN Sentiment Analyst)
**新建文件**: `tradingagents/agents/analysts/cn_sentiment_analyst.py`
- 数据源：东方财富股吧、雪球讨论
- Prompt：中文分析，识别散户情绪、主力动向讨论
- Tools：get_cn_sentiment（新增工具）

### 2.2 政策分析师 (Policy Analyst)
**新建文件**: `tradingagents/agents/analysts/policy_analyst.py`
- 分析央行、证监会、发改委等政策对市场影响
- 识别行业政策利好/利空
- Tools：get_policy_news（新增工具）

### 2.3 资金流分析师 (Fund Flow Analyst)
**新建文件**: `tradingagents/agents/analysts/fund_flow_analyst.py`
- A股：北向资金、主力资金流向、大宗交易
- 加密货币：交易所资金流入流出
- Tools：get_fund_flow（新增工具）

### 2.4 链上分析师 (OnChain Analyst) — 仅加密货币
**新建文件**: `tradingagents/agents/analysts/onchain_analyst.py`
- 巨鲸钱包追踪、合约持仓数据
- Tools：get_onchain_data（新增工具）

### 2.5 注册新 Agent
**修改文件**:
- `tradingagents/agents/utils/agent_states.py` — 新增 report 字段
- `tradingagents/agents/__init__.py` — 导出新 Agent
- `tradingagents/agents/utils/` — 新增工具文件

---

## Phase 3: 工作流适配

### 3.1 修改图编排
**修改文件**: `tradingagents/graph/setup.py`
- 根据 market_type 动态选择分析师组合
- A股：market + fundamentals + cn_sentiment + policy + fund_flow + news
- 加密：market + onchain + fund_flow + news + (sentiment)

### 3.2 条件逻辑
**修改文件**: `tradingagents/graph/conditional_logic.py`
- 为新 Agent 添加条件路由方法

### 3.3 工具节点
**修改文件**: `tradingagents/graph/trading_graph.py`
- 注册新 Agent 的工具节点

---

## Phase 4: 交易逻辑适配

### 4.1 A股规则
- T+1 交易制度
- 涨跌停板（±10%，ST ±5%）
- 集合竞价时段

### 4.2 加密货币规则
- 7×24 全天候交易
- 无涨跌停限制
- 高波动性风控参数调整

### 4.3 实现方式
在 Trader Agent 和 Risk Manager 的 Prompt 中注入市场规则说明。

---

## Phase 5: 中文化

### 5.1 Prompt 中文化
- 所有 Agent 的 System Prompt 增加中文输出指令
- 通过配置 `output_language: "zh"` 控制

### 5.2 报告中文化
- 分析报告、辩论记录、最终决策均输出中文

---

## 文件改动清单

### 新建文件（8个）
1. `tradingagents/dataflows/akshare_provider.py`
2. `tradingagents/dataflows/ccxt_provider.py`
3. `tradingagents/dataflows/cn_news_provider.py`
4. `tradingagents/agents/analysts/cn_sentiment_analyst.py`
5. `tradingagents/agents/analysts/policy_analyst.py`
6. `tradingagents/agents/analysts/fund_flow_analyst.py`
7. `tradingagents/agents/analysts/onchain_analyst.py`
8. `tradingagents/agents/utils/cn_data_tools.py`

### 修改文件（7个）
1. `tradingagents/dataflows/interface.py` — 注册新 vendor
2. `tradingagents/default_config.py` — 新增配置项
3. `tradingagents/agents/utils/agent_states.py` — 新增 state 字段
4. `tradingagents/agents/__init__.py` — 导出新 Agent
5. `tradingagents/graph/trading_graph.py` — 注册工具节点
6. `tradingagents/graph/setup.py` — 添加新 Agent 到工作流
7. `tradingagents/graph/conditional_logic.py` — 添加条件路由

### 依赖新增
- `akshare` — A股数据
- `ccxt` — 加密货币交易所API
