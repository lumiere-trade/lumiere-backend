/**
 * Build initialize escrow instruction (user-based, no strategy_id)
 */

const {
  TransactionInstruction,
  SystemProgram,
  SYSVAR_RENT_PUBKEY,
} = require('@solana/web3.js');
const {
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
} = require('@solana/spl-token');
const { DISCRIMINATORS } = require('./discriminators');

function buildInitializeEscrowInstruction({
  escrow,
  escrowTokenAccount,
  tokenMint,
  user,
  programId,
  bump,
  maxBalance,
}) {
  // Instruction data: discriminator + bump + max_balance
  const bumpBuffer = Buffer.alloc(1);
  bumpBuffer.writeUInt8(bump);

  const maxBalanceBuffer = Buffer.alloc(8);
  maxBalanceBuffer.writeBigUInt64LE(maxBalance);

  const data = Buffer.concat([
    DISCRIMINATORS.INITIALIZE,
    bumpBuffer,
    maxBalanceBuffer,
  ]);

  const keys = [
    { pubkey: escrow, isSigner: false, isWritable: true },
    { pubkey: escrowTokenAccount, isSigner: false, isWritable: true },
    { pubkey: tokenMint, isSigner: false, isWritable: false },
    { pubkey: user, isSigner: true, isWritable: true },
    { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
    { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    {
      pubkey: ASSOCIATED_TOKEN_PROGRAM_ID,
      isSigner: false,
      isWritable: false,
    },
  ];

  return new TransactionInstruction({
    keys,
    programId,
    data,
  });
}

module.exports = { buildInitializeEscrowInstruction };
