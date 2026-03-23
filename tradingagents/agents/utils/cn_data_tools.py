"""Chinese market specific data tools for agents."""

from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_fund_flow(
    ticker: Annotated[str, "Stock symbol (A-share)"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve fund flow data (资金流向) for an A-share stock.
    Shows main force (主力), large (超大单/大单), medium (中单), and small (小单) order flows.
    """
    return route_to_vendor("get_fund_flow", ticker, curr_date)


@tool
def get_north_flow(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve northbound capital flow data (北向资金/沪深港通).
    Shows net inflow from Hong Kong to Shanghai/Shenzhen stock markets.
    Important indicator for A-share market sentiment.
    """
    return route_to_vendor("get_north_flow", curr_date)


@tool
def get_cn_sentiment(
    ticker: Annotated[str, "Stock symbol (A-share)"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve Chinese market sentiment data for a stock.
    Includes institutional participation, market ratings, and discussion heat.
    Data from East Money (东方财富).
    """
    return route_to_vendor("get_cn_sentiment", ticker, curr_date)


@tool
def get_cn_financial_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles"] = 15,
) -> str:
    """
    Retrieve comprehensive Chinese financial news from multiple sources.
    Includes CCTV finance, Sina finance, and economic calendar events.
    """
    return route_to_vendor("get_cn_financial_news", curr_date, look_back_days, limit)


@tool
def get_policy_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    keywords: Annotated[str, "Policy keywords, comma separated"] = "央行,证监会,发改委,国务院",
) -> str:
    """
    Retrieve Chinese policy and regulatory news.
    Filters news by policy keywords and includes macro economic indicators (CPI, PMI).
    Critical for A-share analysis as China's stock market is heavily policy-driven.
    """
    return route_to_vendor("get_policy_news", curr_date, keywords)
