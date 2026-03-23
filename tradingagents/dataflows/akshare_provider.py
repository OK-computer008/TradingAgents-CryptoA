"""AKShare-based data provider for A-share (Chinese stock market) data."""

from typing import Annotated
from datetime import datetime, timedelta
import os
import pandas as pd

try:
    import akshare as ak
except ImportError:
    raise ImportError("akshare is required for A-share data. Install with: pip install akshare")

from .stockstats_utils import StockstatsUtils, _clean_dataframe


def _normalize_symbol(symbol: str) -> str:
    """Normalize A-share symbol format.
    Accepts: 000060.SZ, 000060, sz000060, SZ000060
    Returns clean symbol like '000060' for akshare API calls.
    """
    symbol = symbol.strip().upper()
    # Remove exchange suffix
    if "." in symbol:
        symbol = symbol.split(".")[0]
    # Remove exchange prefix
    for prefix in ("SZ", "SH", "BJ"):
        if symbol.startswith(prefix):
            symbol = symbol[2:]
    return symbol


def _get_exchange_prefix(symbol: str) -> str:
    """Determine exchange prefix for a given stock code."""
    code = _normalize_symbol(symbol)
    if code.startswith(("6",)):
        return "sh"
    elif code.startswith(("0", "3")):
        return "sz"
    elif code.startswith(("4", "8")):
        return "bj"
    return "sz"


def get_stock(
    symbol: Annotated[str, "A-share stock symbol, e.g. '000060.SZ' or '000060'"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get A-share OHLCV data via AKShare."""
    try:
        code = _normalize_symbol(symbol)
        start_fmt = start_date.replace("-", "")
        end_fmt = end_date.replace("-", "")

        # ak.stock_zh_a_hist returns daily historical data
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_fmt,
            end_date=end_fmt,
            adjust="qfq",  # 前复权 (forward-adjusted)
        )

        if df is None or df.empty:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

        # Rename columns to standard OHLCV format
        col_map = {
            "日期": "Date",
            "开盘": "Open",
            "收盘": "Close",
            "最高": "High",
            "最低": "Low",
            "成交量": "Volume",
            "成交额": "Amount",
            "振幅": "Amplitude",
            "涨跌幅": "Change_Pct",
            "涨跌额": "Change",
            "换手率": "Turnover_Rate",
        }
        df = df.rename(columns=col_map)

        # Round numeric columns
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col] = df[col].round(2)

        csv_string = df.to_csv(index=False)

        header = f"# A-share stock data for {symbol} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(df)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# Source: AKShare (前复权)\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving A-share data for {symbol}: {str(e)}"


def get_indicator(
    symbol: Annotated[str, "A-share stock symbol"],
    indicator: Annotated[str, "Technical indicator name"],
    curr_date: Annotated[str, "Current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "Number of days to look back"] = 30,
) -> str:
    """Get technical indicators for A-share stocks using stockstats.

    Uses AKShare for data, stockstats for indicator calculation.
    Supports same indicators as yfinance provider.
    """
    from .config import get_config
    from stockstats import wrap

    best_ind_params = {
        "close_50_sma": "50 SMA: 50日简单移动平均线，中期趋势指标。",
        "close_200_sma": "200 SMA: 200日简单移动平均线，长期趋势基准。",
        "close_10_ema": "10 EMA: 10日指数移动平均线，短期动量捕捉。",
        "macd": "MACD: 移动平均收敛散度，趋势变化信号。",
        "macds": "MACD Signal: MACD信号线，交叉触发交易。",
        "macdh": "MACD Histogram: MACD柱状图，动量强度可视化。",
        "rsi": "RSI: 相对强弱指数，超买(>70)/超卖(<30)识别。",
        "boll": "Bollinger Middle: 布林中轨，20日SMA。",
        "boll_ub": "Bollinger Upper: 布林上轨，超买信号。",
        "boll_lb": "Bollinger Lower: 布林下轨，超卖信号。",
        "atr": "ATR: 平均真实波幅，波动率度量。",
        "vwma": "VWMA: 成交量加权移动平均线。",
        "mfi": "MFI: 资金流量指数，超买(>80)/超卖(<20)。",
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} is not supported. Choose from: {list(best_ind_params.keys())}"
        )

    try:
        config = get_config()
        code = _normalize_symbol(symbol)
        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        before = curr_date_dt - timedelta(days=look_back_days)

        # Fetch enough historical data for indicator calculation (need extra lookback)
        fetch_start = curr_date_dt - timedelta(days=365)
        start_fmt = fetch_start.strftime("%Y%m%d")
        end_fmt = curr_date_dt.strftime("%Y%m%d")

        # Check cache first
        cache_dir = config.get("data_cache_dir", "data")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{symbol}-AKShare-data.csv")

        if os.path.exists(cache_file):
            data = pd.read_csv(cache_file, on_bad_lines="skip")
        else:
            data = ak.stock_zh_a_hist(
                symbol=code, period="daily",
                start_date=fetch_start.strftime("%Y%m%d"),
                end_date=curr_date_dt.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if data is None or data.empty:
                return f"No data found for {symbol}"

            # Rename to standard format for stockstats
            data = data.rename(columns={
                "日期": "Date", "开盘": "Open", "收盘": "Close",
                "最高": "High", "最低": "Low", "成交量": "Volume",
            })
            data.to_csv(cache_file, index=False)

        data = _clean_dataframe(data)
        df = wrap(data)
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        # Calculate indicator
        df[indicator]

        # Build result for requested date range
        ind_string = ""
        current_dt = curr_date_dt
        while current_dt >= before:
            date_str = current_dt.strftime("%Y-%m-%d")
            matching = df[df["Date"] == date_str]
            if not matching.empty:
                val = matching.iloc[0][indicator]
                ind_string += f"{date_str}: {val if pd.notna(val) else 'N/A'}\n"
            else:
                ind_string += f"{date_str}: N/A: 非交易日\n"
            current_dt -= timedelta(days=1)

        result = (
            f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
            + ind_string + "\n\n"
            + best_ind_params.get(indicator, "")
        )
        return result

    except Exception as e:
        return f"Error calculating indicator {indicator} for {symbol}: {str(e)}"


def get_fundamentals(
    ticker: Annotated[str, "A-share stock symbol"],
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Get A-share company fundamentals via AKShare."""
    try:
        code = _normalize_symbol(ticker)

        # Get individual stock info
        df_info = ak.stock_individual_info_em(symbol=code)

        if df_info is None or df_info.empty:
            return f"No fundamentals found for {ticker}"

        # Convert to dict
        info_dict = {}
        for _, row in df_info.iterrows():
            info_dict[row.iloc[0]] = row.iloc[1]

        # Get financial indicators
        try:
            df_indicator = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            fin_summary = ""
            if df_indicator is not None and not df_indicator.empty:
                fin_summary = "\n\n## 财务摘要 (最近报告期):\n"
                fin_summary += df_indicator.head(4).to_string(index=False)
        except Exception:
            fin_summary = ""

        header = f"# A股公司基本面数据: {ticker}\n"
        header += f"# 数据获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# 数据源: AKShare (东方财富)\n\n"

        lines = []
        field_map = {
            "股票代码": "Stock Code",
            "股票简称": "Stock Name",
            "总市值": "Total Market Cap",
            "流通市值": "Float Market Cap",
            "行业": "Industry",
            "上市时间": "IPO Date",
            "总股本": "Total Shares",
            "流通股": "Float Shares",
        }
        for cn_key, en_key in field_map.items():
            if cn_key in info_dict:
                lines.append(f"{en_key} ({cn_key}): {info_dict[cn_key]}")

        return header + "\n".join(lines) + fin_summary

    except Exception as e:
        return f"Error retrieving fundamentals for {ticker}: {str(e)}"


def get_balance_sheet(
    ticker: Annotated[str, "A-share stock symbol"],
    freq: Annotated[str, "Frequency: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Get A-share balance sheet data via AKShare."""
    try:
        code = _normalize_symbol(ticker)
        prefix = _get_exchange_prefix(ticker)
        full_code = f"{prefix}{code}"

        df = ak.stock_balance_sheet_by_report_em(symbol=full_code)

        if df is None or df.empty:
            return f"No balance sheet data found for {ticker}"

        # Take latest 4 periods for quarterly, 2 for annual
        n = 4 if freq == "quarterly" else 2
        df = df.head(n)

        csv_string = df.to_csv(index=False)
        header = f"# Balance Sheet for {ticker} ({freq})\n"
        header += f"# Source: AKShare (东方财富)\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving balance sheet for {ticker}: {str(e)}"


def get_cashflow(
    ticker: Annotated[str, "A-share stock symbol"],
    freq: Annotated[str, "Frequency: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Get A-share cash flow data via AKShare."""
    try:
        code = _normalize_symbol(ticker)
        prefix = _get_exchange_prefix(ticker)
        full_code = f"{prefix}{code}"

        df = ak.stock_cash_flow_sheet_by_report_em(symbol=full_code)

        if df is None or df.empty:
            return f"No cash flow data found for {ticker}"

        n = 4 if freq == "quarterly" else 2
        df = df.head(n)

        csv_string = df.to_csv(index=False)
        header = f"# Cash Flow Statement for {ticker} ({freq})\n"
        header += f"# Source: AKShare (东方财富)\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving cash flow for {ticker}: {str(e)}"


def get_income_statement(
    ticker: Annotated[str, "A-share stock symbol"],
    freq: Annotated[str, "Frequency: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Get A-share income statement data via AKShare."""
    try:
        code = _normalize_symbol(ticker)
        prefix = _get_exchange_prefix(ticker)
        full_code = f"{prefix}{code}"

        df = ak.stock_profit_sheet_by_report_em(symbol=full_code)

        if df is None or df.empty:
            return f"No income statement data found for {ticker}"

        n = 4 if freq == "quarterly" else 2
        df = df.head(n)

        csv_string = df.to_csv(index=False)
        header = f"# Income Statement for {ticker} ({freq})\n"
        header += f"# Source: AKShare (东方财富)\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving income statement for {ticker}: {str(e)}"


def get_news(
    ticker: Annotated[str, "A-share stock symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get A-share stock news via AKShare (东方财富)."""
    try:
        code = _normalize_symbol(ticker)

        # Get stock-specific news from East Money
        df = ak.stock_news_em(symbol=code)

        if df is None or df.empty:
            return f"No news found for {ticker}"

        # Filter by date range
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        news_str = f"## {ticker} A股新闻 ({start_date} 至 {end_date}):\n\n"
        count = 0

        for _, row in df.iterrows():
            try:
                pub_date_str = str(row.get("发布时间", row.get("datetime", "")))
                if pub_date_str:
                    pub_date = pd.to_datetime(pub_date_str)
                    if not (start_dt <= pub_date.replace(tzinfo=None) <= end_dt):
                        continue
            except (ValueError, TypeError):
                pass

            title = row.get("新闻标题", row.get("title", "无标题"))
            content = row.get("新闻内容", row.get("content", ""))
            source = row.get("文章来源", row.get("source", "东方财富"))
            url = row.get("新闻链接", row.get("url", ""))

            news_str += f"### {title} (来源: {source})\n"
            if content:
                # Truncate long content
                news_str += f"{str(content)[:500]}\n"
            if url:
                news_str += f"链接: {url}\n"
            news_str += "\n"
            count += 1

            if count >= 20:
                break

        if count == 0:
            return f"No news found for {ticker} between {start_date} and {end_date}"

        return news_str

    except Exception as e:
        return f"Error fetching news for {ticker}: {str(e)}"


def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles"] = 10,
) -> str:
    """Get Chinese financial market news via AKShare."""
    try:
        # Get CCTV financial news
        df = ak.news_cctv(date=curr_date.replace("-", ""))

        if df is None or df.empty:
            return f"No global news found for {curr_date}"

        news_str = f"## 中国财经新闻 ({curr_date}):\n\n"
        count = 0

        for _, row in df.iterrows():
            title = row.get("title", "")
            content = row.get("content", "")

            if title:
                news_str += f"### {title}\n"
                if content:
                    news_str += f"{str(content)[:300]}\n"
                news_str += "\n"
                count += 1

            if count >= limit:
                break

        if count == 0:
            return f"No news found for {curr_date}"

        return news_str

    except Exception as e:
        return f"Error fetching global news: {str(e)}"


def get_insider_transactions(
    ticker: Annotated[str, "A-share stock symbol"],
) -> str:
    """Get A-share major shareholder changes (大股东增减持)."""
    try:
        code = _normalize_symbol(ticker)

        # Get shareholder changes
        df = ak.stock_gpzy_pledge_ratio_em(symbol=code)

        if df is None or df.empty:
            return f"No insider/pledge data found for {ticker}"

        csv_string = df.head(10).to_csv(index=False)
        header = f"# Shareholder Pledge Data for {ticker}\n"
        header += f"# Source: AKShare\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving insider data for {ticker}: {str(e)}"


# ===== A-Share Specific Data Functions =====

def get_fund_flow(
    ticker: Annotated[str, "A-share stock symbol"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
) -> str:
    """Get individual stock fund flow data (资金流向)."""
    try:
        code = _normalize_symbol(ticker)

        df = ak.stock_individual_fund_flow(stock=code, market=_get_exchange_prefix(ticker))

        if df is None or df.empty:
            return f"No fund flow data found for {ticker}"

        # Take recent 10 trading days
        df = df.tail(10)

        csv_string = df.to_csv(index=False)
        header = f"# 资金流向数据: {ticker} (近10个交易日)\n"
        header += f"# Source: AKShare (东方财富)\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving fund flow for {ticker}: {str(e)}"


def get_north_flow(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
) -> str:
    """Get northbound capital flow data (北向资金)."""
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")

        if df is None or df.empty:
            return "No northbound flow data found"

        # Take recent 10 trading days
        df = df.tail(10)

        csv_string = df.to_csv(index=False)
        header = f"# 北向资金净流入数据 (近10个交易日)\n"
        header += f"# Source: AKShare (东方财富)\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving north flow data: {str(e)}"


def get_cn_sentiment(
    ticker: Annotated[str, "A-share stock symbol"],
    curr_date: Annotated[str, "Current date"],
) -> str:
    """Get stock discussion sentiment from East Money (东方财富股吧热度)."""
    try:
        code = _normalize_symbol(ticker)

        # Get stock comments/posts popularity
        df = ak.stock_comment_detail_zlkp_jgcyd_em(symbol=code)

        result = f"# {ticker} 市场情绪数据\n\n"

        if df is not None and not df.empty:
            result += "## 机构参与度:\n"
            result += df.to_string(index=False)
            result += "\n\n"

        # Also get market sentiment index
        try:
            df_overall = ak.stock_comment_detail_zhpj_lspf_em(symbol=code)
            if df_overall is not None and not df_overall.empty:
                result += "## 综合评价历史评分:\n"
                result += df_overall.tail(10).to_string(index=False)
                result += "\n"
        except Exception:
            pass

        return result

    except Exception as e:
        return f"Error retrieving sentiment for {ticker}: {str(e)}"
