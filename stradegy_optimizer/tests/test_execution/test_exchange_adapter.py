# tests/test_execution/test_exchange_adapter.py
import pytest
import ccxt
import time
from src.execution.exchange_adapter import ExchangeAdapter

@pytest.fixture
def mock_ccxt_exchange(mocker):
    mock_exchange = mocker.Mock(spec=ccxt.binance)
    mock_exchange.id = 'binance'
    mock_exchange.load_markets.return_value = None
    mock_exchange.fetch_ohlcv.return_value = [[1672531200000, 100, 101, 99, 100, 1000]] # Sample candle
    mock_exchange.create_order.return_value = {'id': 'test_order_id', 'status': 'open'}
    mock_exchange.fetch_order.return_value = {'id': 'test_order_id', 'status': 'closed', 'filled': 1.0}
    mock_exchange.fetch_time.return_value = 1672531200000
    mocker.patch('ccxt.binance', return_value=mock_exchange)
    return mock_exchange

@pytest.fixture
def exchange_adapter(test_config, monkeypatch, mock_ccxt_exchange):
    monkeypatch.setenv("EXCHANGE_API_KEY", "dummy_key")
    monkeypatch.setenv("EXCHANGE_SECRET_KEY", "dummy_secret")
    # Adjust rate limit for faster testing if needed
    test_config['system_config']['api']['ccxt']['rate_limit'] = 10 # 10 ms
    return ExchangeAdapter(test_config)

def test_fetch_ohlcv(exchange_adapter, mock_ccxt_exchange):
    symbol = 'BTC/USDT'
    timeframe = '1h'
    ohlcv = exchange_adapter.fetch_ohlcv(symbol, timeframe)
    assert isinstance(ohlcv, list)
    assert len(ohlcv) > 0
    mock_ccxt_exchange.fetch_ohlcv.assert_called_once_with(symbol, timeframe, None, None)

def test_create_order(exchange_adapter, mock_ccxt_exchange):
    symbol = 'BTC/USDT'
    order_type = 'market'
    side = 'buy'
    amount = 0.01
    
    order = exchange_adapter.create_order(symbol, order_type, side, amount)
    assert order['id'] == 'test_order_id'
    assert order['status'] == 'open'
    mock_ccxt_exchange.create_order.assert_called_once_with(symbol, order_type, side, amount, None)

def test_fetch_order_status(exchange_adapter, mock_ccxt_exchange):
    order_id = 'test_order_id'
    status = exchange_adapter.fetch_order_status(order_id)
    assert status['id'] == 'test_order_id'
    assert status['status'] == 'closed'
    mock_ccxt_exchange.fetch_order.assert_called_once_with(order_id, None)

def test_rate_limiting(exchange_adapter, mock_ccxt_exchange, monkeypatch):
    # Ensure initial call is fast
    start_time = time.time()
    exchange_adapter.fetch_ohlcv('BTC/USDT', '1h')
    end_time = time.time()
    assert (end_time - start_time) * 1000 < 50 # Should be fast
    
    # Second call should be delayed by rate_limit
    start_time = time.time()
    exchange_adapter.fetch_ohlcv('BTC/USDT', '1h')
    end_time = time.time()
    # Rate limit is 10ms, so it should take at least that much time more
    assert (end_time - start_time) * 1000 >= exchange_adapter.rate_limit * 1000 - 1
