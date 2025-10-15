/**
 * Instruction discriminators for Escrow program
 * 
 * Auto-generated from Anchor IDL - DO NOT EDIT MANUALLY
 * Source: target/idl/escrow.json
 */

const DISCRIMINATORS = {
  // Initialize escrow (user-based)
  INITIALIZE: Buffer.from([243, 160, 77, 153, 11, 92, 48, 209]),

  // Deposit tokens
  DEPOSIT: Buffer.from([11, 156, 96, 218, 39, 163, 180, 19]),

  // Delegate authorities
  DELEGATE_PLATFORM_AUTHORITY: Buffer.from([
    126, 172, 138, 174, 184, 236, 63, 169,
  ]),
  DELEGATE_TRADING_AUTHORITY: Buffer.from([
    164, 159, 115, 90, 166, 214, 57, 95,
  ]),

  // Revoke authorities
  REVOKE_PLATFORM_AUTHORITY: Buffer.from([
    7, 7, 103, 233, 134, 154, 157, 153,
  ]),
  REVOKE_TRADING_AUTHORITY: Buffer.from([
    207, 57, 250, 223, 186, 166, 244, 101,
  ]),

  // Withdraw operations
  WITHDRAW_SUBSCRIPTION_FEE: Buffer.from([
    203, 153, 47, 13, 242, 238, 168, 197,
  ]),
  WITHDRAW_FOR_TRADE: Buffer.from([94, 156, 46, 103, 177, 6, 178, 118]),
  WITHDRAW: Buffer.from([136, 235, 181, 5, 101, 109, 57, 81]),

  // Emergency withdraw
  EMERGENCY_WITHDRAW: Buffer.from([239, 45, 203, 64, 150, 73, 218, 92]),

  // Pause/Unpause
  PAUSE: Buffer.from([201, 149, 247, 168, 83, 194, 230, 251]),
  UNPAUSE: Buffer.from([90, 30, 199, 250, 91, 20, 91, 20]),

  // Close escrow
  CLOSE: Buffer.from([139, 171, 94, 146, 191, 91, 144, 50]),

  // Set max lifetime
  SET_MAX_LIFETIME: Buffer.from([22, 179, 32, 185, 30, 36, 9, 217]),
};

module.exports = { DISCRIMINATORS };
