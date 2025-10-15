/**
 * Revoke platform/trading authority instructions
 */

const { TransactionInstruction } = require('@solana/web3.js');
const { DISCRIMINATORS } = require('./discriminators');

function buildRevokePlatformAuthorityInstruction({
  escrow,
  user,
  programId,
}) {
  const data = DISCRIMINATORS.REVOKE_PLATFORM_AUTHORITY;

  const keys = [
    { pubkey: escrow, isSigner: false, isWritable: true },
    { pubkey: user, isSigner: true, isWritable: false },
  ];

  return new TransactionInstruction({
    keys,
    programId,
    data,
  });
}

function buildRevokeTradingAuthorityInstruction({ escrow, user, programId }) {
  const data = DISCRIMINATORS.REVOKE_TRADING_AUTHORITY;

  const keys = [
    { pubkey: escrow, isSigner: false, isWritable: true },
    { pubkey: user, isSigner: true, isWritable: false },
  ];

  return new TransactionInstruction({
    keys,
    programId,
    data,
  });
}

module.exports = {
  buildRevokePlatformAuthorityInstruction,
  buildRevokeTradingAuthorityInstruction,
};
