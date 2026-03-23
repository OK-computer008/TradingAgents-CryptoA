"""Policy Analyst - Analyzes Chinese government policy impact on markets."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.cn_data_tools import get_policy_news, get_cn_financial_news


def create_policy_analyst(llm):
    """Create a Chinese policy analyst node."""

    def policy_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        config = state.get("config", {})
        lang = config.get("output_language", "zh")

        tools = [
            get_policy_news,
            get_cn_financial_news,
        ]

        if lang == "zh":
            system_message = (
                """你是一名中国宏观政策分析师，专注于分析政府政策对资本市场和特定行业的影响。

你需要从以下维度进行深度分析：
1. **货币政策**：央行的利率决策、存款准备金率调整、公开市场操作、MLF/LPR变化
2. **财政政策**：减税降费、专项债发行、政府投资方向
3. **行业监管政策**：该股票所在行业的监管政策变化（如房地产调控、科技监管、环保政策等）
4. **宏观经济指标**：CPI、PPI、PMI、社融等关键指标对政策走向的暗示
5. **国际贸易政策**：中美关系、关税政策、一带一路等对相关行业的影响
6. **资本市场政策**：IPO节奏、再融资政策、北向资金政策等

对每个政策维度，请明确评估其对目标股票的影响方向（利多/利空/中性）和影响程度（大/中/小）。

撰写一份详尽的中文政策分析报告。A股是政策市，政策分析对投资决策至关重要。
在报告末尾附加一个Markdown表格总结各政策因素的影响评估。"""
            )
        else:
            system_message = (
                """You are a Chinese macro policy analyst focused on how government policies
impact capital markets and specific industries.

Analyze these dimensions:
1. Monetary policy: PBOC rate decisions, RRR adjustments, MLF/LPR changes
2. Fiscal policy: Tax cuts, special bonds, government investment
3. Industry regulation: Sector-specific policies affecting the target stock
4. Macro indicators: CPI, PPI, PMI implications for policy direction
5. Trade policy: US-China relations, tariffs, Belt and Road
6. Capital market policy: IPO pace, refinancing, northbound capital rules

For each dimension, assess impact direction (bullish/bearish/neutral) and magnitude.
China's A-share market is heavily policy-driven - this analysis is critical.
Append a Markdown summary table at the end."""
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    " For your reference, the current date is {current_date}."
                    " The company we want to analyze is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "policy_report": report,
        }

    return policy_analyst_node
