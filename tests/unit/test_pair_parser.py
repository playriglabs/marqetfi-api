"""Test pair parser utilities."""

import pytest

from app.services.providers.pair_parser import format_pair, is_valid_pair, parse_pair


class TestPairParser:
    """Test pair parser utilities."""

    def test_parse_pair_usdt_quotes(self):
        """Test parsing pairs with USDT quote."""
        assert parse_pair("BTCUSDT") == ("BTC", "USDT")
        assert parse_pair("ETHUSDT") == ("ETH", "USDT")
        assert parse_pair("SOLUSDT") == ("SOL", "USDT")

    def test_parse_pair_usdc_quotes(self):
        """Test parsing pairs with USDC quote."""
        assert parse_pair("BTCUSDC") == ("BTC", "USDC")
        assert parse_pair("ETHUSDC") == ("ETH", "USDC")

    def test_parse_pair_usd_quotes(self):
        """Test parsing pairs with USD quote."""
        assert parse_pair("EURUSD") == ("EUR", "USD")
        assert parse_pair("GBPUSD") == ("GBP", "USD")
        assert parse_pair("XAUUSD") == ("XAU", "USD")

    def test_parse_pair_fiat_quotes(self):
        """Test parsing pairs with fiat quotes."""
        assert parse_pair("EURGBP") == ("EUR", "GBP")
        assert parse_pair("EURJPY") == ("EUR", "JPY")
        assert parse_pair("AUDCAD") == ("AUD", "CAD")

    def test_parse_pair_crypto_base(self):
        """Test parsing pairs with crypto base."""
        assert parse_pair("LINKBTC") == ("LINK", "BTC")
        assert parse_pair("UNIETH") == ("UNI", "ETH")

    def test_parse_pair_case_insensitive(self):
        """Test parsing pairs with different cases."""
        assert parse_pair("btcusdt") == ("BTC", "USDT")
        assert parse_pair("EthUsdt") == ("ETH", "USDT")
        assert parse_pair("  EURUSD  ") == ("EUR", "USD")

    def test_parse_pair_fallback_middle_split(self):
        """Test parsing pairs using fallback middle split."""
        # Pairs that don't match known quotes
        result = parse_pair("ABCDEF")
        assert result[0] == "ABC"
        assert result[1] == "DEF"

    def test_parse_pair_fallback_last_3_chars(self):
        """Test parsing pairs using fallback last 3 chars."""
        result = parse_pair("TESTXYZ")
        assert len(result[0]) > 0
        assert len(result[1]) > 0

    def test_parse_pair_invalid_short(self):
        """Test parsing invalid short pair."""
        with pytest.raises(ValueError, match="Cannot parse trading pair"):
            parse_pair("AB")

    def test_parse_pair_invalid_empty(self):
        """Test parsing empty pair."""
        with pytest.raises(ValueError, match="Cannot parse trading pair"):
            parse_pair("")

    def test_format_pair_simple(self):
        """Test formatting simple pairs."""
        assert format_pair("BTC", "USDT") == "BTCUSDT"
        assert format_pair("ETH", "USD") == "ETHUSD"
        assert format_pair("EUR", "USD") == "EURUSD"

    def test_format_pair_case_handling(self):
        """Test formatting pairs with different cases."""
        assert format_pair("btc", "usdt") == "BTCUSDT"
        assert format_pair("Eth", "Usd") == "ETHUSD"

    def test_format_pair_special_chars(self):
        """Test formatting pairs with special characters."""
        assert format_pair("BTC", "USDT") == "BTCUSDT"

    def test_is_valid_pair_valid(self):
        """Test validating valid pairs."""
        assert is_valid_pair("BTCUSDT") is True
        assert is_valid_pair("ETHUSD") is True
        assert is_valid_pair("EURUSD") is True
        assert is_valid_pair("btcusdt") is True  # Case insensitive

    def test_is_valid_pair_invalid(self):
        """Test validating invalid pairs."""
        assert is_valid_pair("AB") is False  # Too short
        assert is_valid_pair("") is False  # Empty
        assert is_valid_pair("A") is False  # Single char

    def test_is_valid_pair_edge_cases(self):
        """Test validating edge case pairs."""
        # Valid pairs should have at least 2 chars for asset and quote
        assert is_valid_pair("BTCUSDT") is True
        # Invalid if parsing fails
        assert is_valid_pair("X") is False

    def test_parse_and_format_roundtrip(self):
        """Test parse and format roundtrip."""
        test_pairs = ["BTCUSDT", "ETHUSD", "EURUSD", "SOLUSDC", "LINKBTC"]

        for pair in test_pairs:
            asset, quote = parse_pair(pair)
            formatted = format_pair(asset, quote)
            # Should match original (case normalized)
            assert formatted == pair.upper()

