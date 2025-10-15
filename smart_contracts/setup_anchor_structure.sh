#!/usr/bin/env bash

################################################################################
# Setup Anchor Project Structure
#
# This script creates the proper Anchor workspace structure for the escrow
# smart contract project.
################################################################################

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

echo -e "${BLUE}Setting up Anchor project structure...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Create directory structure
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p programs/escrow/src
mkdir -p tests
mkdir -p migrations
mkdir -p app

# Move existing source files to proper location
echo -e "${BLUE}Moving source files...${NC}"
if [ -d "src" ]; then
    cp src/*.rs programs/escrow/src/
    echo -e "${GREEN}✓ Source files moved to programs/escrow/src/${NC}"
fi

# Create Anchor.toml
echo -e "${BLUE}Creating Anchor.toml...${NC}"
cat > Anchor.toml << 'EOF'
# Anchor configuration file

[toolchain]
anchor_version = "0.31.1"

[features]
seeds = true
skip-lint = false
resolution = true

[programs.localnet]
escrow = "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"

[programs.devnet]
escrow = "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"

[programs.mainnet]
escrow = "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"

[registry]
url = "https://api.apr.dev"

[provider]
cluster = "Devnet"
wallet = "/root/lumiere/keypair.json"

[scripts]
test = "yarn run ts-mocha -p ./tsconfig.json -t 1000000 tests/**/*.ts"

[test]
startup_wait = 10000

[test.validator]
url = "https://api.devnet.solana.com"
EOF

echo -e "${GREEN}✓ Anchor.toml created${NC}"

# Create root Cargo.toml
echo -e "${BLUE}Creating root Cargo.toml...${NC}"
cat > Cargo.toml << 'EOF'
[workspace]
members = [
    "programs/*"
]
resolver = "2"

[profile.release]
overflow-checks = true
lto = "fat"
codegen-units = 1

[profile.release.build-override]
opt-level = 3
incremental = false
codegen-units = 1
EOF

echo -e "${GREEN}✓ Root Cargo.toml created${NC}"

# Create program Cargo.toml
echo -e "${BLUE}Creating programs/escrow/Cargo.toml...${NC}"
cat > programs/escrow/Cargo.toml << 'EOF'
[package]
name = "escrow"
version = "0.1.0"
description = "Secure SPL token escrow for trading strategies"
edition = "2021"

[lib]
crate-type = ["cdylib", "lib"]
name = "escrow"

[features]
no-entrypoint = []
no-idl = []
cpi = ["no-entrypoint"]
default = []

[dependencies]
anchor-lang = "0.31.1"
anchor-spl = "0.31.1"

[dev-dependencies]
solana-program-test = "~2.0"
solana-sdk = "~2.0"
spl-token = { version = "6.0", features = ["no-entrypoint"] }
EOF

echo -e "${GREEN}✓ Program Cargo.toml created${NC}"

# Create Xargo.toml
echo -e "${BLUE}Creating programs/escrow/Xargo.toml...${NC}"
cat > programs/escrow/Xargo.toml << 'EOF'
[target.bpfel-unknown-unknown.dependencies.std]
features = []
EOF

echo -e "${GREEN}✓ Xargo.toml created${NC}"

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "${BLUE}Creating .gitignore...${NC}"
    cat > .gitignore << 'EOF'
.anchor
.DS_Store
target
**/*.rs.bk
node_modules
test-ledger
.yarn
logs/*.log
EOF
    echo -e "${GREEN}✓ .gitignore created${NC}"
fi

# Create migrations/deploy.ts
echo -e "${BLUE}Creating migrations/deploy.ts...${NC}"
cat > migrations/deploy.ts << 'EOF'
// Migrations are an early feature. Currently, they're nothing more than this
// single deploy script that's invoked from the CLI, injecting a provider
// configured from the workspace's Anchor.toml.

const anchor = require("@coral-xyz/anchor");

module.exports = async function (provider) {
  // Configure client to use the provider.
  anchor.setProvider(provider);

  // Add your deploy script here.
};
EOF

echo -e "${GREEN}✓ migrations/deploy.ts created${NC}"

# Create package.json
echo -e "${BLUE}Creating package.json...${NC}"
cat > package.json << 'EOF'
{
  "name": "escrow",
  "version": "0.1.0",
  "description": "Secure SPL token escrow smart contract",
  "license": "Apache-2.0",
  "scripts": {
    "lint:fix": "prettier */*.js \"*/**/*{.js,.ts}\" -w",
    "lint": "prettier */*.js \"*/**/*{.js,.ts}\" --check"
  },
  "dependencies": {
    "@coral-xyz/anchor": "^0.31.1"
  },
  "devDependencies": {
    "@types/bn.js": "^5.1.0",
    "@types/chai": "^4.3.0",
    "@types/mocha": "^9.0.0",
    "chai": "^4.3.4",
    "mocha": "^9.0.3",
    "ts-mocha": "^10.0.0",
    "typescript": "^4.3.5",
    "prettier": "^2.6.2"
  }
}
EOF

echo -e "${GREEN}✓ package.json created${NC}"

# Create tsconfig.json
echo -e "${BLUE}Creating tsconfig.json...${NC}"
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "types": ["mocha", "chai"],
    "typeRoots": ["./node_modules/@types"],
    "lib": ["es2015"],
    "module": "commonjs",
    "target": "es6",
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
EOF

echo -e "${GREEN}✓ tsconfig.json created${NC}"

# Show final structure
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Anchor project structure created!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project structure:"
tree -L 3 -I 'target|node_modules|.anchor'

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run: anchor build"
echo "2. Run: ./deploy_escrow.sh --environment dev"
echo ""
echo -e "${BLUE}Note: The program ID in Anchor.toml is a placeholder.${NC}"
echo -e "${BLUE}After first deployment, update it with your actual program ID.${NC}"
