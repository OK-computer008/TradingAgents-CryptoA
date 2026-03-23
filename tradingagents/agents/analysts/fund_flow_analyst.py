"""Fund Flow Analyst - Analyzes capital flow patterns for A-shares and crypto."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.cn_data_tools import get_fund_flow, get_north_flow


def create_fund_flow_analyst(llm):
    """Create a fund flow analyst node."""

    def fund_flow_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        config = state.get("config", {})
        lang = config.get("output_language", "zh")

        tools = [
            get_fund_flow,
            get_north_flow,
        ]

        if lang == "zh":
            system_message = (
                """你是一名资金流向分析师，专注于追踪和分析市场资金的流动方向。

你需要分析以下维度的资金数据：
1. **个股资金流向**：主力资金（超大单+大单）的净流入/流出，中单和小单的流向
2. **北向资金（沪深港通）**：外资通过港股通流入A股的趋势，这是A股最重要的增量资金指标之一
3. **资金流向趋势**：连续多日的资金流向变化，识别持续流入/流出的信号
4. **主力行为解读**：通过资金数据推断主力机构的操作意图（建仓/洗盘/出货）

分析要点：
- 主力净流入为正 → 可能在建仓或加仓
- 主力净流出 + 股价上涨 → 可能是出货信号
- 北向资金大幅流入 → 外资看好，通常是积极信号
- 超大单净流入 > 大单净流入 → 大机构在操作

请撰写一份详尽的资金流向分析报告，包含具体数据和趋势判断。
在报告末尾附加Markdown表格总结资金流向关键数据。"""
            )
        else:
            system_message = (
                """You are a fund flow analyst tracking capital movement patterns.

Analyze these dimensions:
1. Individual stock fund flow: Main force (large orders) net inflow/outflow
2. Northbound capital (Stock Connect): Foreign capital flow trends into A-shares
3. Flow trends: Multi-day patterns identifying sustained inflow/outflow
4. Institutional behavior: Infer intentions (accumulation/distribution/washout)

Key signals:
- Net main force inflow → potential accumulation
- Net outflow + price rise → possible distribution
- Large northbound inflow → positive foreign sentiment
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
            "fund_flow_report": report,
        }

    return fund_flow_analyst_node
