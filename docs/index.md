# Lumiere Public Documentation

Welcome to the Lumiere open-source components documentation.

## Overview

Lumiere is a DeFi algorithmic trading platform built on Solana, providing transparent and secure user-facing infrastructure.

## Components

### Pourtier - User Management
FastAPI service handling user authentication, subscriptions, and escrow management.

[API Reference →](api/pourtier/main.md)

### Passeur - Blockchain Bridge
Bridge service connecting Python backend to Solana smart contracts.

[API Reference →](api/passeur/bridge/server.md)

### Courier - Event Bus
WebSocket-based event distribution for real-time updates.

[API Reference →](api/courier/broker.md)

### Shared - Common Libraries
Utilities, blockchain helpers, and technical indicators.

[API Reference →](api/shared/courier_client.md)

### Laborant - Test Framework
Smart test orchestrator with git change detection.

[API Reference →](api/laborant/cli.md)

## Getting Started

1. Clone the repository
2. Install dependencies
3. Follow component-specific setup guides

## Links

- [GitHub Repository](https://github.com/lumiere-trade/lumiere-public)
- [Website](https://lumiere.trade)
