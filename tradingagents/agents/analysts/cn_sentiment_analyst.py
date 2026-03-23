"""Chinese Sentiment Analyst - Analyzes market sentiment from Chinese social media and forums."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.cn_data_tools import get_cn_sentiment, get_cn_financial_news
from tradingagents.agents.utils.agent_utils import get_news


def create_cn_sentiment_analyst(llm):
    """Create a Chinese market sentiment analyst node."""

    def cn_sentiment_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        config = state.get("config", {})
        lang = config.get("output_language", "zh")

        tools = [
            get_cn_sentiment,
            get_news,
            get_cn_financial_news,
        ]

        if lang == "zh":
            system_message = (
                """你是一名中国A股市场情绪分析师。你的任务是分析特定股票在过去一周内的市场情绪和舆论动向。

你需要从以下维度进行全面分析：
1. **机构参与度**：机构投资者的买卖动向和持仓变化
2. **市场讨论热度**：东方财富股吧、雪球等平台的讨论热度和情绪倾向
3. **综合评价评分**：市场对该股票的综合评价变化趋势
4. **散户情绪**：通过社交媒体和论坛判断散户的情绪状态（恐慌/贪婪/观望）
5. **新闻情绪**：近期新闻对该股票情绪的正面/负面影响

请撰写一份详尽的中文情绪分析报告，包含具体数据和深度洞察。
不要简单地说"情绪混合"，请提供细粒度的分析和判断。
在报告末尾附加一个Markdown表格总结关键发现。"""
            )
        else:
            system_message = (
                """You are a Chinese A-share market sentiment analyst. Analyze market sentiment
and public opinion for the given stock over the past week.

Analyze from these dimensions:
1. Institutional participation and position changes
2. Discussion heat from Chinese forums (East Money, Xueqiu)
3. Comprehensive market ratings and score trends
4. Retail investor sentiment (fear/greed/neutral)
5. News sentiment impact

Write a detailed report with specific data and deep insights.
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
            "cn_sentiment_report": report,
        }

    return cn_sentiment_analyst_node
