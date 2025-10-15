/**
 * Close escrow instruction
 */

const { TransactionInstruction } = require('@solana/web3.js');
const { TOKEN_PROGRAM_ID } = require('@solana/spl-token');
const { DISCRIMINATORS } = require('./discriminators');

function buildCloseEscrowInstruction({
  escrow,
  escrowTokenAccount,
  user,
  programId,
}) {
  const data = DISCRIMINATORS.CLOSE;

  const keys = [
    { pubkey: escrow, isSigner: false, isWritable: true },
    { pubkey: escrowTokenAccount, isSigner: false, isWritable: true },
    { pubkey: user, isSigner: true, isWritable: true },
    { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
  ];

  return new TransactionInstruction({
    keys,
    programId,
    data,
  });
}

module.exports = { buildCloseEscrowInstruction };
