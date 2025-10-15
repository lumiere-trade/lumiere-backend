# Passeur - Blockchain Bridge Service

**Bridge service connecting Python backend to Solana smart contracts.**

---

## Overview

Passeur acts as a bridge between Lumiere's Python backend services and Solana blockchain smart contracts. It provides a clean abstraction layer for blockchain interactions, handling transaction signing, verification, and escrow operations.

**Name Origin:** *Passeur* (French) = "ferryman" or "one who helps cross"

---

## Features

### Escrow Operations
- Initialize escrow accounts
- Deposit USDC to escrow
- Withdraw funds from escrow
- Query escrow balances
- Delegate trading authority

### Transaction Management
- Transaction signing with keypairs
- Signature verification
- Transaction status tracking
- Error handling and retries

### Bridge Architecture
- Python CLI wrapper
- Node.js bridge server (WebSocket)
- Solana Web3.js integration
- Circuit breaker for fault tolerance

---

## Architecture
```
Python Services (Pourtier)
       │
       ├──► PasseurBridgeClient (Python)
       │         │
       │         ├──► HTTP REST API
       │         └──► WebSocket (events)
       │
       └──► Bridge Server (Node.js)
                 │
                 ├──► Solana Web3.js
                 └──► Smart Contract (Anchor)
                       │
                       └──► Solana RPC
```

### Components

**Python Layer:**
- `PasseurBridgeClient` - HTTP client for bridge communication
- `PasseurQueryService` - Read-only blockchain queries
- `cli/bridge.py` - Command-line interface
- `utils/blockchain.py` - Helper functions

**Node.js Bridge:**
- `bridge/server.js` - Express WebSocket server
- `bridge/instructions/` - Solana instruction builders
- Transaction handling and signing

---

## Quick Start

### Prerequisites
```bash
# System requirements
Python 3.11+
Node.js 18+
Solana CLI
```

### Installation
```bash
# Install Python dependencies
pip install -e .

# Install Node.js bridge dependencies
cd bridge
npm install
```

### Configuration

Create `passeur/config/passeur.yaml`:
```yaml
# Bridge Server
BRIDGE_URL: "http://localhost:8767"
BRIDGE_HOST: "127.0.0.1"
BRIDGE_PORT: 8767

# Solana
SOLANA_RPC_URL: "https://api.devnet.solana.com"
SOLANA_NETWORK: "devnet"
ESCROW_PROGRAM_ID: "your-program-id-here"

# Keypairs
AUTHORITY_KEYPAIR_PATH: "/path/to/authority.json"
PLATFORM_KEYPAIR_PATH: "/path/to/platform.json"

# Environment
ENV: "development"
```

### Run Bridge Server
```bash
# Start Node.js bridge
cd passeur/bridge
node server.js

# Bridge available at http://localhost:8767
```

### Run Python Client
```bash
# Example: Initialize escrow
python -m passeur.cli.bridge initialize-escrow \
  --user-wallet <wallet-address> \
  --token-mint <usdc-mint>

# Example: Get balance
python -m passeur.cli.bridge get-balance \
  --escrow-account <escrow-address>
```

---

## API Endpoints (Bridge Server)

### Escrow Operations
```bash
POST   /initialize-escrow         # Initialize new escrow account
POST   /deposit                   # Deposit USDC to escrow
POST   /withdraw                  # Withdraw from escrow
GET    /balance/:escrow           # Get escrow balance
```

### Authority Management
```bash
POST   /delegate-authority        # Delegate trading authority
POST   /revoke-authority          # Revoke trading authority
```

### Transaction Status
```bash
GET    /transaction/:signature    # Get transaction status
POST   /verify-signature          # Verify transaction signature
```

---

## Python Usage

### Using PasseurBridgeClient
```python
from passeur.infrastructure.blockchain import PasseurBridgeClient

# Initialize client
client = PasseurBridgeClient(
    bridge_url="http://localhost:8767",
    timeout=30.0
)

# Initialize escrow
result = await client.initialize_escrow(
    user_wallet="wallet-address",
    token_mint="usdc-mint-address"
)

# Get balance
balance = await client.get_escrow_balance(
    escrow_account="escrow-address"
)

print(f"Balance: {balance}")
```

### Using CLI
```bash
# Initialize escrow
python -m passeur.cli.bridge initialize-escrow \
  --user-wallet 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU \
  --token-mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v

# Deposit funds
python -m passeur.cli.bridge deposit \
  --escrow-account <address> \
  --amount 1000.50 \
  --user-keypair /path/to/user.json

# Withdraw funds
python -m passeur.cli.bridge withdraw \
  --escrow-account <address> \
  --amount 500.00 \
  --destination <wallet-address>
```

---

## Testing
```bash
# Run integration tests (requires bridge server running)
pytest passeur/tests/integration/

# E2E tests (requires Solana localnet)
pytest passeur/tests/e2e/

# Specific test
python -m passeur.tests.integration.test_bridge_lifecycle
```

---

## Development

### Code Standards

- **PEP8 compliant** for Python
- **StandardJS** for Node.js
- **Type hints** for all Python functions
- **JSDoc** comments for JavaScript

### Bridge Server Development
```bash
# Watch mode (auto-restart)
cd passeur/bridge
npm run dev

# Run with debug logging
DEBUG=* node server.js
```

### Adding New Instructions

1. Create instruction builder in `bridge/instructions/`
2. Add discriminator in `discriminators.js`
3. Export from `index.js`
4. Add endpoint in `server.js`
5. Add Python client method in `PasseurBridgeClient`

Example:
```javascript
// bridge/instructions/new_instruction.js
export function buildNewInstruction(params) {
  const instruction = {
    programId: ESCROW_PROGRAM_ID,
    keys: [...],
    data: Buffer.from([...])
  };
  return instruction;
}
```

---

## Error Handling

### Circuit Breaker

Passeur includes a circuit breaker to prevent cascading failures:
```python
from passeur.infrastructure.blockchain import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,    # Open after 5 failures
    timeout=60,             # Stay open for 60 seconds
    expected_exception=ConnectionError
)

@breaker
async def call_blockchain():
    # Protected operation
    pass
```

**States:**
- **Closed:** Normal operation
- **Open:** All calls fail fast (no blockchain calls)
- **Half-Open:** Testing if service recovered

---

## Security

### Keypair Management

- Authority keypairs stored securely (not in git)
- User keypairs never stored server-side
- Transaction signing happens in bridge (isolated)
- Private keys never exposed to API

### Transaction Verification
```python
# Verify transaction before processing
is_valid = await client.verify_transaction(signature)
if not is_valid:
    raise InvalidTransactionError()
```

---

## Monitoring

### Health Check
```bash
GET http://localhost:8767/health

Response:
{
  "status": "healthy",
  "solana_rpc": "connected",
  "program_deployed": true
}
```

### Metrics

Bridge exposes metrics for monitoring:
- Transaction success/failure rates
- Response times
- RPC connection status
- Circuit breaker state

---

## Troubleshooting

### Bridge Won't Start
```bash
# Check Node.js version
node --version  # Should be 18+

# Check if port is available
lsof -i :8767

# Check Solana RPC connectivity
curl https://api.devnet.solana.com -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

### Transaction Failures
```bash
# Check Solana logs
solana logs <signature>

# Verify program deployment
solana program show <program-id>

# Check account balances
solana balance <wallet-address>
```

---

## Related Components

- [Pourtier](../pourtier) - Uses Passeur for escrow operations
- [Smart Contracts](../smart_contracts) - Deployed programs
- [Shared](../shared) - Common blockchain utilities

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

**Questions?** Open an issue or contact: dev@lumiere.trade
