#!/bin/bash
# Refactor ISmartContractClient → IEscrowContractClient

cd ~/lumiere/pourtier

# 1. Rename interface file
mv domain/services/i_smart_contract_client.py \
   domain/services/i_escrow_contract_client.py

# 2. Rename implementation file  
mv infrastructure/blockchain/solana_contract_client.py \
   infrastructure/blockchain/escrow_contract_client.py

# 3. Update class name in implementation
sed -i 's/class SolanaContractClient/class EscrowContractClient/g' \
  infrastructure/blockchain/escrow_contract_client.py

# 4. Update all imports: interface
find . -type f -name "*.py" -exec sed -i \
  's/from pourtier\.domain\.services\.i_smart_contract_client import/from pourtier.domain.services.i_escrow_contract_client import/g' {} +

find . -type f -name "*.py" -exec sed -i \
  's/ISmartContractClient/IEscrowContractClient/g' {} +

# 5. Update all imports: implementation
find . -type f -name "*.py" -exec sed -i \
  's/from pourtier\.infrastructure\.blockchain\.solana_contract_client import/from pourtier.infrastructure.blockchain.escrow_contract_client import/g' {} +

find . -type f -name "*.py" -exec sed -i \
  's/SolanaContractClient/EscrowContractClient/g' {} +

# 6. Update variable names
find . -type f -name "*.py" -exec sed -i \
  's/smart_contract_client/escrow_contract_client/g' {} +

find . -type f -name "*.py" -exec sed -i \
  's/_smart_contract_client/_escrow_contract_client/g' {} +

# 7. Update config keys
find . -type f -name "*.py" -exec sed -i \
  's/SMART_CONTRACT_PROGRAM_ID/ESCROW_PROGRAM_ID/g' {} +

find . -type f -name "*.yaml" -exec sed -i \
  's/SMART_CONTRACT_PROGRAM_ID/ESCROW_PROGRAM_ID/g' {} +

# 8. Rename test file
mv tests/integration/services/test_smart_contract_client.py \
   tests/integration/services/test_escrow_contract_client.py 2>/dev/null || true

echo "✅ Refactoring complete!"
