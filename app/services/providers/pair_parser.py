"""Trading pair parser for combined format."""


def parse_pair(pair: str) -> tuple[str, str]:
    """Parse a combined trading pair into asset and quote.

    Examples:
        "BTCUSDT" -> ("BTC", "USDT")
        "EURUSD" -> ("EUR", "USD")
        "ETHUSDT" -> ("ETH", "USDT")
        "XAUUSD" -> ("XAU", "USD")

    Args:
        pair: Combined trading pair (e.g., BTCUSDT, EURUSD)

    Returns:
        Tuple of (asset, quote)

    Raises:
        ValueError: If pair cannot be parsed
    """
    pair = pair.upper().strip()

    # Common quote currencies (ordered by length, longest first)
    common_quotes = [
        "USDT",
        "USDC",
        "BUSD",
        "DAI",  # Stablecoins
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CHF",
        "AUD",
        "CAD",
        "NZD",  # Fiat
        "BTC",
        "ETH",  # Crypto base
    ]

    # Try to match known quote currencies
    for quote in common_quotes:
        if pair.endswith(quote):
            asset = pair[: -len(quote)]
            if asset:
                return (asset, quote)

    # Fallback: try to split at common patterns
    # For pairs like "EURUSD", try splitting at 3 chars (EUR/USD)
    if len(pair) >= 6:
        # Try splitting in the middle
        mid = len(pair) // 2
        asset = pair[:mid]
        quote = pair[mid:]
        if asset and quote:
            return (asset, quote)

    # Last resort: assume last 3-4 chars are quote
    if len(pair) >= 6:
        quote = pair[-3:]
        asset = pair[:-3]
        return (asset, quote)
    elif len(pair) >= 4:
        quote = pair[-3:]
        asset = pair[:-3]
        return (asset, quote)

    raise ValueError(f"Cannot parse trading pair: {pair}")


def format_pair(asset: str, quote: str) -> str:
    """Format asset and quote into combined pair format.

    Args:
        asset: Asset symbol (e.g., BTC, EUR)
        quote: Quote currency (e.g., USDT, USD)

    Returns:
        Combined pair (e.g., BTCUSDT, EURUSD)
    """
    return f"{asset.upper()}{quote.upper()}"


def is_valid_pair(pair: str) -> bool:
    """Check if a pair string is valid.

    Args:
        pair: Trading pair string

    Returns:
        True if valid, False otherwise
    """
    try:
        asset, quote = parse_pair(pair)
        return bool(asset and quote and len(asset) >= 2 and len(quote) >= 2)
    except ValueError:
        return False
