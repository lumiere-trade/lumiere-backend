# Lumiere Public Components

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Solana](https://img.shields.io/badge/Solana-Devnet-14F195?logo=solana)](https://solana.com)

**Open-source components of the Lumiere DeFi algorithmic trading platform.**

## Why Open Source?

We believe **transparency builds trust** in DeFi. Users should see exactly how their:
- Wallet authentication works
- Subscriptions are managed
- Funds interact with blockchain escrow
- Data is stored and protected

This repository contains all user-facing components of Lumiere, allowing anyone to audit our code and verify our claims.

---

## Components

### Pourtier - User Management & Subscriptions

FastAPI-based user management service with wallet authentication.

**Features:**
- Solana wallet-based authentication (no passwords!)
- Subscription management (Basic/Pro plans)
- Escrow account integration
- Legal compliance tracking
- Multi-layer caching (L1 memory + L2 Redis)
- Prometheus monitoring

**Tech Stack:** Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy 2.0, Redis

**[Documentation](./pourtier/README.md)**

---

### Passeur - Blockchain Bridge

Bridge service connecting Python backend to Solana smart contracts.

**Features:**
- Escrow contract interaction
- Transaction signing & verification
- WebSocket event streaming
- Circuit breaker pattern for resilience

**Tech Stack:** Python 3.11+, Node.js bridge, Solana Web3.js

**[Documentation](./passeur/README.md)**

---

### Courier - Event Bus

WebSocket-based event distribution system for real-time updates.

**Features:**
- Pub/sub event routing
- Room-based subscriptions
- Cross-service communication
- Real-time client updates

**Tech Stack:** Python 3.11+, WebSockets

**[Documentation](./courier/README.md)**

---

### Shared - Common Libraries

Shared utilities used across all Lumiere services.

**Includes:**
- Blockchain helpers (Solana client, transaction signing)
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- System reporter with emoji logging
- Test framework (LaborantTest)

**Tech Stack:** Python 3.11+, Solders (Solana)

**[Documentation](./shared/README.md)**

---

### Smart Contracts - Solana Programs

Escrow smart contracts deployed on Solana blockchain.

**Features:**
- Non-custodial escrow (users maintain control)
- Delegated authority for trading
- Withdraw functionality
- Event emission for tracking

**Tech Stack:** Rust, Anchor Framework, Solana

**Deployed:**
- Devnet: `[Coming Soon]`
- Mainnet: `[Not Yet Deployed]`

**[Documentation](./smart_contracts/README.md)**

---

### Laborant - Test Framework

Custom async test runner for the Lumiere ecosystem.

**Features:**
- Component-aware test execution
- Change detection for smart test runs
- Code quality checks
- JSON result output for CI/CD

**Tech Stack:** Python 3.11+

**[Documentation](./laborant/README.md)**

---

## Architecture
```
┌─────────────┐
│   Client    │ (Web/Mobile)
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────┐
│         Pourtier API                │
│  (User Management, Subscriptions)   │
└────────┬────────────────────────────┘
         │
    ├────┼────► Redis (Caching)
    │    │
    │    └────► Courier (Event Bus)
    │           │
    │           └──► [Private: Trading Engine]
    │
    └────► Passeur (Blockchain Bridge)
           │
           └──► Solana RPC
```

**Note:** Trading algorithms, AI strategy builder, and market analysis components are **proprietary** and not included in this repository.

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Node.js 18+ (for Passeur bridge)
- Solana CLI (for smart contracts)

### Quick Start

Each component has its own setup instructions. See individual README files:

- [Pourtier Setup](./pourtier/README.md)
- [Passeur Setup](./passeur/README.md)
- [Smart Contracts Setup](./smart_contracts/README.md)

---

## Security

### Reporting Vulnerabilities

We take security seriously. If you discover a vulnerability:

1. **DO NOT** open a public issue
2. Email: security@lumiere.trade
3. Include detailed reproduction steps
4. Allow 48 hours for initial response

### Audit Status

- **Smart Contracts:** [Pending Audit]
- **API Security:** Internal review completed
- **Infrastructure:** Ongoing monitoring

---

## Contributing

We welcome contributions to improve transparency and security!

### How to Contribute

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- Follow PEP8 (Python) / Standard (JavaScript)
- Add tests for new features
- Update documentation
- All commits must be signed

---

## License

This project is licensed under the **Apache License 2.0**.

See [LICENSE](./LICENSE) for details.

**TL;DR:** You can use, modify, and distribute this code freely, even commercially, as long as you:
- Include the original license
- State any significant changes
- Don't use our trademarks without permission

---

## Links

- **Website:** [lumiere.trade](https://lumiere.trade)
- **Documentation:** [Coming Soon]
- **Twitter:** [Coming Soon]
- **Discord:** [Coming Soon]

---

## FAQ

**Q: Is the entire Lumiere platform open source?**

A: No. User-facing components (auth, subscriptions, blockchain integration) are open source for transparency. Proprietary components include trading algorithms, AI strategy generation, and market analysis.

**Q: Can I run my own Lumiere instance?**

A: Yes, but you'll only have the user management and blockchain interaction layers. The trading engine is proprietary.

**Q: How do you make money if core components are open source?**

A: Our revenue comes from subscription fees for access to proprietary trading algorithms and AI-powered strategy generation.

**Q: Are user funds safe?**

A: Yes. Funds are stored in non-custodial Solana escrow accounts controlled by users. We only have delegated trading authority, not withdrawal rights. Audit the smart contracts yourself!

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Solana](https://solana.com/)
- [Anchor Framework](https://www.anchor-lang.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- And many other amazing open source projects

---

**Made with a lot of passion by the Lumiere team**

*Building transparent, secure, and profitable DeFi trading infrastructure on Solana.*
