# Shared - Common Libraries

**Shared utilities and libraries used across all Lumiere services.**

---

## Overview

The Shared module provides common functionality used by all Lumiere components, including blockchain utilities, technical indicators, system reporting, and testing frameworks.

**Purpose:** Eliminate code duplication and provide consistent implementations across services.

---

## Components

### Blockchain Utilities

**Location:** `shared/blockchain/`

Solana blockchain interaction utilities.

**Modules:**
- `solana_client.py` - Solana RPC client wrapper
- `transaction_signer.py` - Transaction signing utilities
- `wallets.py` - Platform wallet management
- `escrow_helpers.py` - Escrow contract helpers

**Example Usage:**
```python
from shared.blockchain import SolanaClient
from shared.blockchain.wallets import PlatformWallets

# Initialize client
client = SolanaClient(
    rpc_url="https://api.devnet.solana.com",
    commitment="confirmed"
)

# Get platform wallet
platform_wallet = PlatformWallets.get_platform_wallet()

# Get test wallets
alice_address = PlatformWallets.get_test_alice_address()
```

---

### Technical Indicators

**Location:** `shared/indicators/`

Technical analysis indicators for trading strategies.

**Available Indicators:**
- `rsi.py` - Relative Strength Index
- `macd.py` - Moving Average Convergence Divergence
- `bb.py` - Bollinger Bands
- `ema.py` - Exponential Moving Average
- `sma.py` - Simple Moving Average
- `atr.py` - Average True Range
- `adx.py` - Average Directional Index
- `stochastic.py` - Stochastic Oscillator
- `volume.py` - Volume indicators
- `patterns.py` - Chart pattern detection

**Example Usage:**
```python
from shared.indicators import RSI, MACD, BollingerBands

# Calculate RSI
rsi = RSI(period=14)
rsi_value = rsi.calculate(price_data)

# Calculate MACD
macd = MACD(fast=12, slow=26, signal=9)
macd_line, signal_line, histogram = macd.calculate(price_data)

# Calculate Bollinger Bands
bb = BollingerBands(period=20, std_dev=2)
upper, middle, lower = bb.calculate(price_data)
```

---

### System Reporter

**Location:** `shared/reporter/`

Structured logging and reporting system with emoji support.

**Features:**
- Color-coded log levels
- Context tracking
- Verbose levels (0-3)
- Emoji categories for visual identification
- File and console output

**Example Usage:**
```python
from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji

reporter = SystemReporter(
    name="my_service",
    log_dir="logs",
    verbose=1
)

# Log messages
reporter.info(
    f"{Emoji.SUCCESS} Operation completed",
    context="Service"
)

reporter.error(
    f"{Emoji.ERROR} Operation failed: {error}",
    context="Service"
)

reporter.debug(
    f"{Emoji.SYSTEM.READY} Debug info",
    context="Service",
    verbose_level=2
)
```

**Emoji Categories:**
- `Emoji.SUCCESS` - Success indicators
- `Emoji.ERROR` - Error indicators
- `Emoji.WARNING` - Warning indicators
- `Emoji.SYSTEM.*` - System events
- `Emoji.NETWORK.*` - Network events
- `Emoji.DATABASE.*` - Database events
- `Emoji.TRADING.*` - Trading events

---

### Courier Client

**Location:** `shared/courier_client.py`

WebSocket client for Courier event bus.

**Example Usage:**
```python
from shared.courier_client import CourierClient

# Initialize client
courier = CourierClient(url="ws://localhost:8766/ws/my_channel")

# Connect
await courier.connect()

# Send event (if publisher)
await courier.send({
    "type": "event.occurred",
    "data": {"key": "value"}
})

# Listen for events (if subscriber)
async for event in courier.listen():
    if event['type'] == 'ping':
        continue  # Skip heartbeat
    
    print(f"Event: {event}")
    await handle_event(event)

# Disconnect
await courier.disconnect()
```

---

### Test Framework

**Location:** `shared/tests/`

LaborantTest base class and testing utilities.

**Features:**
- Async test support
- Setup/teardown hooks
- Test categorization (unit/integration/e2e)
- Component mapping
- Result schema validation

**Example Usage:**
```python
from shared.tests import LaborantTest

class TestMyFeature(LaborantTest):
    """Integration tests for my feature."""
    
    component_name = "my_service"
    test_category = "integration"
    
    async def async_setup(self):
        """Setup before all tests."""
        self.client = await create_test_client()
    
    async def async_teardown(self):
        """Cleanup after all tests."""
        await self.client.close()
    
    async def async_setup_test(self):
        """Setup before each test."""
        await self.clear_test_data()
    
    async def test_feature_works(self):
        """Test that feature works correctly."""
        result = await self.client.call_feature()
        assert result == expected_value
```

---

## Installation
```bash
# Install as editable package
pip install -e .

# Or install from parent directory
cd /root/lumiere
pip install -e shared/
```

---

## Dependencies

Core dependencies:
- `solders` - Solana Python library
- `httpx` - Async HTTP client
- `websockets` - WebSocket support
- `pandas` - Data manipulation (for indicators)
- `numpy` - Numerical computing (for indicators)

---

## Project Structure
```
shared/
├── blockchain/              # Blockchain utilities
│   ├── solana_client.py
│   ├── transaction_signer.py
│   ├── wallets.py
│   ├── escrow_helpers.py
│   └── keypairs/           # Keypair storage (gitignored)
│       ├── production/
│       └── test/
├── indicators/             # Technical indicators
│   ├── base.py            # Base indicator class
│   ├── rsi.py
│   ├── macd.py
│   ├── bb.py
│   └── ...
├── reporter/              # System reporter
│   ├── system_reporter.py
│   └── emojis/           # Emoji definitions
│       ├── base_emojis.py
│       ├── trading_emojis.py
│       └── ...
├── tests/                 # Test framework
│   ├── test_base.py      # LaborantTest base class
│   ├── models.py
│   └── result_schema.py
├── courier_client.py      # Courier WebSocket client
└── pyproject.toml        # Package configuration
```

---

## Usage Examples

### Platform Wallets
```python
from shared.blockchain.wallets import PlatformWallets, Environment
import os

# Set environment
os.environ['LUMIERE_ENV'] = 'production'

# Get production platform wallet
wallet = PlatformWallets.get_platform_wallet()

# Get test wallets
alice = PlatformWallets.get_test_alice_address()
bob = PlatformWallets.get_test_bob_address()
authority = PlatformWallets.get_test_authority_address()

# Get keypair paths
platform_keypair = PlatformWallets.get_test_platform_keypair()
```

### Indicator Calculation
```python
from shared.indicators import RSI, MACD
import pandas as pd

# Load price data
df = pd.DataFrame({
    'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
})

# Calculate RSI
rsi = RSI(period=14)
df['rsi'] = rsi.calculate(df['close'])

# Calculate MACD
macd = MACD(fast=12, slow=26, signal=9)
macd_data = macd.calculate(df['close'])
df['macd'] = macd_data['macd']
df['signal'] = macd_data['signal']
df['histogram'] = macd_data['histogram']

print(df)
```

### System Reporting
```python
from shared.reporter import SystemReporter
from shared.reporter.emojis import Emoji

reporter = SystemReporter(
    name="strategy_engine",
    log_dir="logs/strategy",
    verbose=2
)

# Different log levels
reporter.debug("Debugging info", verbose_level=3)
reporter.info(f"{Emoji.SYSTEM.STARTUP} Service starting")
reporter.warning(f"{Emoji.WARNING} High memory usage")
reporter.error(f"{Emoji.ERROR} Connection failed", exc_info=True)

# With context
reporter.info(
    f"{Emoji.SUCCESS} Trade executed",
    context="OrderManager",
    extra_data={"order_id": "123", "price": 100.50}
)
```

---

## Testing
```bash
# Run shared tests
pytest shared/tests/

# Run with coverage
pytest shared/tests/ --cov=shared --cov-report=html
```

---

## Development

### Adding New Indicators

1. Create indicator file in `shared/indicators/`
2. Inherit from `BaseIndicator`
3. Implement `calculate()` method
4. Add to `__init__.py`
5. Write tests

Example:
```python
from shared.indicators.base import BaseIndicator
import pandas as pd

class MyIndicator(BaseIndicator):
    """Custom indicator implementation."""
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, data: pd.Series) -> pd.Series:
        """Calculate indicator values."""
        # Implementation here
        return result
```

### Adding New Emoji Categories

1. Create emoji file in `shared/reporter/emojis/`
2. Define emoji constants
3. Export from `__init__.py`

---

## Best Practices

### Blockchain Operations
- Always use environment-specific wallets
- Never commit keypairs to git
- Use test wallets for development
- Verify transactions before processing

### Indicators
- Validate input data before calculation
- Handle edge cases (insufficient data)
- Use appropriate periods for timeframes
- Document calculation methodology

### Logging
- Use appropriate log levels
- Include context in log messages
- Use emojis for visual identification
- Set verbose levels appropriately

---

## Related Components

- [Pourtier](../pourtier) - Uses blockchain utilities
- [Passeur](../passeur) - Uses blockchain utilities
- [Courier](../courier) - Uses system reporter
- All components - Use shared utilities

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

**Questions?** Open an issue or contact: dev@lumiere.trade
