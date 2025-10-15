/**
 * Instruction builders index
 */

const {
  buildInitializeEscrowInstruction,
} = require('./initialize_escrow');
const {
  buildDelegatePlatformAuthorityInstruction,
  buildDelegateTradingAuthorityInstruction,
} = require('./delegate_authority');
const {
  buildRevokePlatformAuthorityInstruction,
  buildRevokeTradingAuthorityInstruction,
} = require('./revoke_authority');
const { buildWithdrawInstruction } = require('./withdraw');
const { buildCloseEscrowInstruction } = require('./close_escrow');
const { DISCRIMINATORS } = require('./discriminators');

module.exports = {
  buildInitializeEscrowInstruction,
  buildDelegatePlatformAuthorityInstruction,
  buildDelegateTradingAuthorityInstruction,
  buildRevokePlatformAuthorityInstruction,
  buildRevokeTradingAuthorityInstruction,
  buildWithdrawInstruction,
  buildCloseEscrowInstruction,
  DISCRIMINATORS,
};
