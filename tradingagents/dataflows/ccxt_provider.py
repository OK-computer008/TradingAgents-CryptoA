"""CCXT-based data provider for cryptocurrency market data."""

from typing import Annotated
from datetime import datetime, timedelta
import os
import pandas as pd

try:
    import ccxt
except ImportError:
    raise ImportError("ccxt is required for crypto data. Install with: pip install ccxt")

from .stockstats_utils import _clean_dataframe


def _get_exchange(exchange_id: str = "binance") -> ccxt.Exchange:
    """Create and return a CCXT exchange instance."""
    exchange_class = getattr(ccxt, exchange_id, None)
    if exchange_class is None:
        raise ValueError(f"Exchange '{exchange_id}' not supported by CCXT")
    return exchange_class({"enableRateLimit": True})


def _normalize_symbol(symbol: str) -> str:
    """Normalize crypto symbol to CCXT format.
    Accepts: BTC/USDT, BTCUSDT, btc-usdt, BTC_USDT
    Returns: BTC/USDT
    """
    symbol = symbol.strip().upper()
    # Already in correct format
    if "/" in symbol:
        return symbol
    # Handle common separators
    for sep in ("-", "_"):
        if sep in symbol:
            parts = symbol.split(sep)
            return f"{parts[0]}/{parts[1]}"
    # Try to split common pairs (BTCUSDT -> BTC/USDT)
    quote_currencies = ["USDT", "USDC", "BUSD", "USD", "BTC", "ETH", "BNB"]
    for quote in quote_currencies:
        if symbol.endswith(quote) and len(symbol) > len(quote):
            base = symbol[:-len(quote)]
            return f"{base}/{quote}"
    return symbol


def get_stock(
    symbol: Annotated[str, "Crypto trading pair, e.g. 'BTC/USDT' or 'BTCUSDT'"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get cryptocurrency OHLCV data via CCXT."""
    try:
        from .config import get_config
        config = get_config()
        exchange_id = config.get("crypto_exchange", "binance")

        exchange = _get_exchange(exchange_id)
        pair = _normalize_symbol(symbol)

        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

        all_ohlcv = []
        since = start_ts

        while since < end_ts:
            ohlcv = exchange.fetch_ohlcv(pair, timeframe="1d", since=since, limit=500)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            if len(ohlcv) < 500:
                break

        if not all_ohlcv:
            return f"No data found for '{symbol}' between {start_date} and {end_date}"

        df = pd.DataFrame(all_ohlcv, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms").dt.strftime("%Y-%m-%d")

        # Filter to date range
        df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

        # Round prices
        for col in ["Open", "High", "Low", "Close"]:
            df[col] = df[col].round(2)

        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        csv_string = df.to_csv(index=False)

        header = f"# Crypto OHLCV data for {pair} from {start_date} to {end_date}\n"
        header += f"# Exchange: {exchange_id}\n"
        header += f"# Total records: {len(df)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving crypto data for {symbol}: {str(e)}"


def get_indicator(
    symbol: Annotated[str, "Crypto trading pair"],
    indicator: Annotated[str, "Technical indicator name"],
    curr_date: Annotated[str, "Current date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "Number of days to look back"] = 30,
) -> str:
    """Get technical indicators for crypto using stockstats."""
    from .config import get_config
    from stockstats import wrap

    best_ind_params = {
        "close_50_sma": "50 SMA: 50-day simple moving average.",
        "close_200_sma": "200 SMA: 200-day simple moving average.",
        "close_10_ema": "10 EMA: 10-day exponential moving average.",
        "macd": "MACD: Moving average convergence divergence.",
        "macds": "MACD Signal: Signal line for MACD crossovers.",
        "macdh": "MACD Histogram: Momentum strength visualization.",
        "rsi": "RSI: Relative strength index (70=overbought, 30=oversold).",
        "boll": "Bollinger Middle: 20-day SMA.",
        "boll_ub": "Bollinger Upper: Upper band (+2 std dev).",
        "boll_lb": "Bollinger Lower: Lower band (-2 std dev).",
        "atr": "ATR: Average true range, volatility measure.",
        "vwma": "VWMA: Volume-weighted moving average.",
        "mfi": "MFI: Money flow index (80=overbought, 20=oversold).",
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} not supported. Choose from: {list(best_ind_params.keys())}"
        )

    try:
        config = get_config()
        exchange_id = config.get("crypto_exchange", "binance")
        exchange = _get_exchange(exchange_id)
        pair = _normalize_symbol(symbol)

        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        before = curr_date_dt - timedelta(days=look_back_days)

        # Fetch enough data for indicator calculation
        fetch_start = curr_date_dt - timedelta(days=365)
        start_ts = int(fetch_start.timestamp() * 1000)
        end_ts = int(curr_date_dt.timestamp() * 1000)

        # Check cache
        cache_dir = config.get("data_cache_dir", "data")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{pair.replace('/', '-')}-CCXT-data.csv")

        if os.path.exists(cache_file):
            data = pd.read_csv(cache_file, on_bad_lines="skip")
        else:
            all_ohlcv = []
            since = start_ts
            while since < end_ts:
                ohlcv = exchange.fetch_ohlcv(pair, timeframe="1d", since=since, limit=500)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                if len(ohlcv) < 500:
                    break

            if not all_ohlcv:
                return f"No data found for {symbol}"

            data = pd.DataFrame(all_ohlcv, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
            data["Date"] = pd.to_datetime(data["Timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
            data = data[["Date", "Open", "High", "Low", "Close", "Volume"]]
            data.to_csv(cache_file, index=False)

        data = _clean_dataframe(data)
        df = wrap(data)
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        # Calculate indicator
        df[indicator]

        # Build result
        ind_string = ""
        current_dt = curr_date_dt
        while current_dt >= before:
            date_str = current_dt.strftime("%Y-%m-%d")
            matching = df[df["Date"] == date_str]
            if not matching.empty:
                val = matching.iloc[0][indicator]
                ind_string += f"{date_str}: {val if pd.notna(val) else 'N/A'}\n"
            else:
                ind_string += f"{date_str}: N/A\n"
            current_dt -= timedelta(days=1)

        result = (
            f"## {indicator} values for {pair} from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
            + ind_string + "\n\n"
            + best_ind_params.get(indicator, "")
        )
        return result

    except Exception as e:
        return f"Error calculating indicator {indicator} for {symbol}: {str(e)}"


def get_fundamentals(
    ticker: Annotated[str, "Crypto trading pair"],
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Get basic crypto market info. Note: crypto has no traditional fundamentals."""
    try:
        from .config import get_config
        config = get_config()
        exchange_id = config.get("crypto_exchange", "binance")
        exchange = _get_exchange(exchange_id)
        pair = _normalize_symbol(ticker)

        # Load markets to get pair info
        exchange.load_markets()

        if pair not in exchange.markets:
            return f"Trading pair {pair} not found on {exchange_id}"

        market = exchange.markets[pair]
        ticker_data = exchange.fetch_ticker(pair)

        info = []
        info.append(f"# Crypto Market Data: {pair}")
        info.append(f"# Exchange: {exchange_id}")
        info.append(f"# Data retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if ticker_data:
            info.append(f"Last Price: {ticker_data.get('last', 'N/A')}")
            info.append(f"24h High: {ticker_data.get('high', 'N/A')}")
            info.append(f"24h Low: {ticker_data.get('low', 'N/A')}")
            info.append(f"24h Volume: {ticker_data.get('quoteVolume', 'N/A')}")
            info.append(f"24h Change: {ticker_data.get('percentage', 'N/A')}%")
            info.append(f"Bid: {ticker_data.get('bid', 'N/A')}")
            info.append(f"Ask: {ticker_data.get('ask', 'N/A')}")
            info.append(f"VWAP: {ticker_data.get('vwap', 'N/A')}")

        if market:
            info.append(f"\nBase Currency: {market.get('base', 'N/A')}")
            info.append(f"Quote Currency: {market.get('quote', 'N/A')}")
            info.append(f"Contract Type: {'Spot' if market.get('spot') else 'Derivative'}")

        info.append("\nNote: Cryptocurrencies do not have traditional financial statements.")
        info.append("Evaluate based on: on-chain metrics, tokenomics, development activity,")
        info.append("exchange flows, and market sentiment instead.")

        return "\n".join(info)

    except Exception as e:
        return f"Error retrieving crypto info for {ticker}: {str(e)}"


def get_balance_sheet(
    ticker: Annotated[str, "Crypto trading pair"],
    freq: Annotated[str, "Not applicable for crypto"] = "quarterly",
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Not applicable for crypto - returns explanation."""
    return (
        f"Balance sheets are not applicable for cryptocurrencies like {ticker}. "
        "Crypto assets do not have traditional corporate financial statements. "
        "For on-chain analysis, consider: TVL (Total Value Locked), "
        "treasury holdings, protocol revenue, and token supply metrics."
    )


def get_cashflow(
    ticker: Annotated[str, "Crypto trading pair"],
    freq: Annotated[str, "Not applicable for crypto"] = "quarterly",
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Not applicable for crypto - returns explanation."""
    return (
        f"Cash flow statements are not applicable for cryptocurrencies like {ticker}. "
        "For DeFi protocols, consider: protocol fees, treasury inflows/outflows, "
        "staking rewards, and burn mechanisms."
    )


def get_income_statement(
    ticker: Annotated[str, "Crypto trading pair"],
    freq: Annotated[str, "Not applicable for crypto"] = "quarterly",
    curr_date: Annotated[str, "Current date"] = None,
) -> str:
    """Not applicable for crypto - returns explanation."""
    return (
        f"Income statements are not applicable for cryptocurrencies like {ticker}. "
        "For token evaluation, consider: trading volume trends, "
        "market cap rank, holder distribution, and development activity."
    )


def get_news(
    ticker: Annotated[str, "Crypto symbol or pair"],
    start_date: Annotated[str, "Start date"],
    end_date: Annotated[str, "End date"],
) -> str:
    """Crypto news is not natively supported by CCXT. Returns guidance."""
    pair = _normalize_symbol(ticker)
    return (
        f"CCXT does not provide news data for {pair}. "
        "For crypto news analysis, the framework uses the configured news_data vendor. "
        "Consider using yfinance or a dedicated crypto news API."
    )


def get_global_news(
    curr_date: Annotated[str, "Current date"],
    look_back_days: Annotated[int, "Days to look back"] = 7,
    limit: Annotated[int, "Max articles"] = 10,
) -> str:
    """Global crypto news not supported by CCXT. Falls back to other vendors."""
    return (
        "CCXT does not provide global news data. "
        "The framework will fall back to yfinance or other configured news vendors."
    )


def get_insider_transactions(
    ticker: Annotated[str, "Crypto symbol"],
) -> str:
    """Not applicable for crypto."""
    pair = _normalize_symbol(ticker)
    return (
        f"Insider transactions are not applicable for {pair}. "
        "For crypto, monitor: whale wallet movements, exchange inflows/outflows, "
        "and large on-chain transfers instead."
    )
