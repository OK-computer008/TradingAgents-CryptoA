"""Chinese financial news data provider using AKShare and web scraping."""

from typing import Annotated, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re
import pandas as pd

try:
    import akshare as ak
except ImportError:
    raise ImportError("akshare is required for Chinese news. Install with: pip install akshare")


# ===== News quality filter =====

_AD_KEYWORDS = [
    "开户", "手续费", "理财产品推荐", "免费领取", "限时优惠", "点击领取",
    "扫码关注", "加群", "返佣", "低佣金", "薅羊毛", "红包",
]


def _title_similarity(a: str, b: str) -> float:
    """Compute title similarity ratio (0-1)."""
    return SequenceMatcher(None, a, b).ratio()


def _is_relevant(title: str, ticker: str) -> bool:
    """Check if a news title is relevant to the given ticker."""
    # Extract stock code and name parts from ticker (e.g. "000060.SZ" -> "000060")
    code = re.sub(r"\.\w+$", "", ticker)
    if code and code in title:
        return True
    # For crypto tickers like "BTC/USDT"
    parts = re.split(r"[/.\-]", ticker)
    return any(p and p in title for p in parts if len(p) >= 2)


def filter_news(
    raw_news: list,
    ticker: Optional[str] = None,
    max_age_days: int = 7,
    similarity_threshold: float = 0.8,
    ref_date: Optional[str] = None,
) -> list:
    """Filter news list for quality: dedup, remove ads, enforce freshness, check relevance.

    Args:
        raw_news: List of dicts with at least 'title' key. Optional: 'date', 'content'.
        ticker: If provided, boost relevance filtering for this ticker.
        max_age_days: Discard news older than this many days.
        similarity_threshold: Title similarity above this deduplicates (keeps latest).
        ref_date: Reference date (yyyy-mm-dd) for freshness check. Defaults to today.

    Returns:
        Filtered list of news dicts.
    """
    if not raw_news:
        return raw_news

    ref_dt = datetime.strptime(ref_date, "%Y-%m-%d") if ref_date else datetime.now()
    cutoff_dt = ref_dt - timedelta(days=max_age_days)

    filtered = []
    for item in raw_news:
        title = item.get("title", "")
        if not title:
            continue

        # Ad filter
        if any(kw in title for kw in _AD_KEYWORDS):
            continue
        if item.get("content") and any(kw in item["content"] for kw in _AD_KEYWORDS):
            continue

        # Freshness filter
        date_str = item.get("date", "")
        if date_str:
            try:
                item_dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
                if item_dt < cutoff_dt:
                    continue
            except (ValueError, TypeError):
                pass  # Keep items with unparseable dates

        # Dedup: skip if too similar to an already-kept title
        is_dup = False
        for kept in filtered:
            if _title_similarity(title, kept["title"]) > similarity_threshold:
                is_dup = True
                break
        if is_dup:
            continue

        # Relevance tagging (non-blocking — just annotate)
        if ticker:
            item["relevant"] = _is_relevant(title, ticker)

        filtered.append(item)

    # If ticker provided, sort relevant items first
    if ticker:
        filtered.sort(key=lambda x: (not x.get("relevant", False)))

    return filtered


def get_cn_financial_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles"] = 15,
    ticker: Annotated[Optional[str], "Optional ticker for relevance filtering"] = None,
) -> str:
    """Get Chinese financial market news from multiple sources."""
    news_str = f"## 中国财经新闻综合 ({curr_date}, 回溯{look_back_days}天):\n\n"
    total_count = 0
    raw_items = []  # Collect for filtering

    # Source 1: CCTV financial news (央视财经新闻)
    try:
        date_str = curr_date.replace("-", "")
        df = ak.news_cctv(date=date_str)
        if df is not None and not df.empty:
            for _, row in df.head(limit).iterrows():
                title = row.get("title", "")
                content = row.get("content", "")
                if title:
                    raw_items.append({
                        "title": title,
                        "content": str(content)[:200] if content else "",
                        "source": "cctv",
                        "date": curr_date,
                    })
    except Exception as e:
        news_str += f"央视财经新闻获取失败: {str(e)}\n\n"

    # Source 2: Financial news from major portals (财经要闻)
    try:
        df2 = ak.stock_news_main_sina()
        if df2 is not None and not df2.empty:
            for _, row in df2.head(limit).iterrows():
                title = row.get("标题", row.get("title", ""))
                time_str = row.get("时间", row.get("time", ""))
                url = row.get("链接", row.get("url", ""))
                if title:
                    raw_items.append({
                        "title": title,
                        "content": "",
                        "source": "sina",
                        "date": str(time_str)[:10] if time_str else "",
                        "time": str(time_str),
                        "url": str(url) if url else "",
                    })
    except Exception:
        pass

    # Source 3: Economic calendar events
    try:
        df3 = ak.news_economic_baidu(date=curr_date.replace("-", ""))
        if df3 is not None and not df3.empty:
            for _, row in df3.head(limit).iterrows():
                event = row.get("事件", row.get("event", ""))
                if event:
                    raw_items.append({
                        "title": str(event),
                        "content": "",
                        "source": "calendar",
                        "date": curr_date,
                    })
    except Exception:
        pass

    # Apply quality filter
    filtered_items = filter_news(raw_items, ticker=ticker, max_age_days=look_back_days, ref_date=curr_date)

    # Format output by source
    cctv_items = [i for i in filtered_items if i.get("source") == "cctv"]
    sina_items = [i for i in filtered_items if i.get("source") == "sina"]
    cal_items = [i for i in filtered_items if i.get("source") == "calendar"]

    if cctv_items:
        news_str += "### 一、央视财经新闻:\n\n"
        for item in cctv_items[:limit // 3]:
            news_str += f"**{item['title']}**\n"
            if item.get("content"):
                news_str += f"{item['content']}\n"
            news_str += "\n"
            total_count += 1

    if sina_items:
        news_str += "### 二、新浪财经要闻:\n\n"
        for item in sina_items[:limit // 3]:
            news_str += f"**{item['title']}**"
            if item.get("time"):
                news_str += f" ({item['time']})"
            news_str += "\n"
            if item.get("url"):
                news_str += f"链接: {item['url']}\n"
            news_str += "\n"
            total_count += 1

    if cal_items:
        news_str += "### 三、经济日历/事件:\n\n"
        for item in cal_items[:limit // 3]:
            news_str += f"- {item['title']}\n"
            total_count += 1

    if total_count == 0:
        return f"未找到 {curr_date} 的中国财经新闻"

    return news_str


def get_policy_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    keywords: Annotated[str, "Policy keywords to search, comma separated"] = "央行,证监会,发改委,国务院",
    ticker: Annotated[Optional[str], "Optional ticker for relevance filtering"] = None,
) -> str:
    """Get Chinese policy and regulatory news."""
    news_str = f"## 中国政策与监管新闻 ({curr_date}):\n\n"
    total_count = 0
    raw_items = []

    # Get CCTV news and filter for policy keywords
    try:
        date_str = curr_date.replace("-", "")
        df = ak.news_cctv(date=date_str)

        if df is not None and not df.empty:
            keyword_list = [k.strip() for k in keywords.split(",")]

            for _, row in df.iterrows():
                title = str(row.get("title", ""))
                content = str(row.get("content", ""))
                text = title + content

                # Check if any keyword matches
                matched = [kw for kw in keyword_list if kw in text]
                if matched:
                    raw_items.append({
                        "title": title,
                        "content": content[:300] if content else "",
                        "date": curr_date,
                        "matched_keywords": matched,
                    })

                if len(raw_items) >= 20:  # Collect more, filter later
                    break
    except Exception as e:
        news_str += f"政策新闻获取失败: {str(e)}\n"

    # Apply quality filter
    filtered_items = filter_news(raw_items, ticker=ticker, ref_date=curr_date)

    for item in filtered_items[:10]:
        kws = item.get("matched_keywords", [])
        news_str += f"**{item['title']}** [关键词: {', '.join(kws)}]\n"
        if item.get("content"):
            news_str += f"{item['content']}\n"
        news_str += "\n"
        total_count += 1

    # Also get macro economic indicators
    try:
        news_str += "\n### 近期重要经济指标:\n\n"

        # CPI data
        try:
            df_cpi = ak.macro_china_cpi_monthly()
            if df_cpi is not None and not df_cpi.empty:
                latest_cpi = df_cpi.tail(3)
                news_str += "**CPI (月度):**\n"
                news_str += latest_cpi.to_string(index=False) + "\n\n"
        except Exception:
            pass

        # PMI data
        try:
            df_pmi = ak.macro_china_pmi()
            if df_pmi is not None and not df_pmi.empty:
                latest_pmi = df_pmi.tail(3)
                news_str += "**PMI (制造业):**\n"
                news_str += latest_pmi.to_string(index=False) + "\n\n"
        except Exception:
            pass

    except Exception:
        pass

    if total_count == 0 and "经济指标" not in news_str:
        return f"未找到 {curr_date} 的相关政策新闻"

    return news_str
