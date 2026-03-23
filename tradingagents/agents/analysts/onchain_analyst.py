"""OnChain Analyst - Analyzes on-chain data for cryptocurrency markets."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_stock_data, get_news


def create_onchain_analyst(llm):
    """Create a cryptocurrency on-chain analyst node.

    Note: On-chain data requires specialized APIs (Dune, DefiLlama, Glassnode).
    This analyst currently works with available exchange data and prompts the LLM
    to provide on-chain insights based on its knowledge. Future versions can integrate
    dedicated on-chain data providers.
    """

    def onchain_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        config = state.get("config", {})
        lang = config.get("output_language", "en")

        tools = [
            get_stock_data,
            get_news,
        ]

        system_message = (
            """You are a cryptocurrency on-chain analyst specializing in blockchain data analysis.

Your task is to analyze the given cryptocurrency/token from an on-chain perspective.

Based on the trading data available and your knowledge, analyze:
1. **Trading Volume Patterns**: Unusual volume spikes, volume profile analysis
2. **Exchange Flows**: Likely exchange inflow/outflow patterns based on volume changes
3. **Whale Activity Indicators**: Large order patterns visible in price/volume data
4. **Market Microstructure**: Bid-ask spread implications, order book depth analysis
5. **Token-specific Factors**:
   - Supply dynamics (inflation/deflation schedule, unlock events)
   - Staking yield trends
   - DeFi TVL implications
   - Network activity indicators

Since direct on-chain API access is limited, use your expert knowledge of blockchain
metrics to provide qualitative analysis supplemented by the quantitative exchange data.

For major tokens (BTC, ETH), reference common on-chain metrics:
- MVRV ratio trends
- Exchange reserve changes
- Active addresses patterns
- Hash rate / staking participation
- Funding rates in perpetual markets

Write a detailed on-chain analysis report.
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
                    " The asset we want to analyze is {ticker}",
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
            "onchain_report": report,
        }

    return onchain_analyst_node
