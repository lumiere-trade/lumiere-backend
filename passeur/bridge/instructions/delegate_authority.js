/**
 * Delegate platform/trading authority instructions
 */

const { TransactionInstruction } = require('@solana/web3.js');
const { DISCRIMINATORS } = require('./discriminators');

function buildDelegatePlatformAuthorityInstruction({
  escrow,
  user,
  authority,
  programId,
}) {
  // Data: discriminator + authority pubkey (32 bytes)
  const data = Buffer.concat([
    DISCRIMINATORS.DELEGATE_PLATFORM_AUTHORITY,
    authority.toBuffer(),
  ]);

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

function buildDelegateTradingAuthorityInstruction({
  escrow,
  user,
  authority,
  programId,
}) {
  // Data: discriminator + authority pubkey (32 bytes)
  const data = Buffer.concat([
    DISCRIMINATORS.DELEGATE_TRADING_AUTHORITY,
    authority.toBuffer(),
  ]);

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
  buildDelegatePlatformAuthorityInstruction,
  buildDelegateTradingAuthorityInstruction,
};
