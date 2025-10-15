/**
 * Withdraw instructions (user withdrawal)
 */

const { TransactionInstruction } = require('@solana/web3.js');
const { TOKEN_PROGRAM_ID } = require('@solana/spl-token');
const { DISCRIMINATORS } = require('./discriminators');

function buildWithdrawInstruction({
  escrow,
  escrowTokenAccount,
  userTokenAccount,
  tokenMint,
  user,
  programId,
  amount,
}) {
  // Data: discriminator + amount (u64)
  const amountBuffer = Buffer.alloc(8);
  amountBuffer.writeBigUInt64LE(amount);
  const data = Buffer.concat([DISCRIMINATORS.WITHDRAW, amountBuffer]);

  const keys = [
    { pubkey: escrow, isSigner: false, isWritable: true },
    { pubkey: escrowTokenAccount, isSigner: false, isWritable: true },
    { pubkey: userTokenAccount, isSigner: false, isWritable: true },
    { pubkey: tokenMint, isSigner: false, isWritable: false },
    { pubkey: user, isSigner: true, isWritable: true },
    { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
  ];

  return new TransactionInstruction({
    keys,
    programId,
    data,
  });
}

module.exports = { buildWithdrawInstruction };
