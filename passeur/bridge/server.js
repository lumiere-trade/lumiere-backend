/**
 * Passeur Bridge Server - User-Based Escrow
 *
 * HTTP/WebSocket bridge between Pourtier backend and Solana escrow
 * smart contract. Pure Solana SDK implementation (no Anchor).
 *
 * Architecture: User-based escrow (ONE escrow per user)
 * - No strategy_id in PDA derivation
 * - Platform authority (Pourtier) for subscription fees
 * - Trading authority (Chevalier) for trade execution
 * - PDA seeds: ["escrow", user_pubkey]
 */

// Load environment variables from .env file
require('dotenv').config({ path: require('path').join(__dirname, '..', `.env.${process.env.ENV || 'production'}`) });

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const {
  Connection,
  PublicKey,
  Keypair,
  Transaction,
  TransactionInstruction,
} = require('@solana/web3.js');
const {
  TOKEN_PROGRAM_ID,
  getAssociatedTokenAddress,
} = require('@solana/spl-token');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Import instruction builders
const {
  buildInitializeEscrowInstruction,
  buildDelegatePlatformAuthorityInstruction,
  buildDelegateTradingAuthorityInstruction,
  buildRevokePlatformAuthorityInstruction,
  buildRevokeTradingAuthorityInstruction,
  buildWithdrawSubscriptionFeeInstruction,
  buildWithdrawForTradeInstruction,
  buildWithdrawInstruction,
  buildCloseEscrowInstruction,
  DISCRIMINATORS,
} = require('./instructions');

// ============================================================
// CONFIGURATION - Hybrid Approach (YAML + ENV)
// ============================================================

/**
 * Load configuration from YAML file and environment variables.
 *
 * Priority: Environment variables > YAML config > defaults
 *
 * YAML configs (default.yaml, development.yaml, production.yaml, test.yaml):
 * - bridge_host, bridge_port (non-sensitive, environment-specific)
 * - heartbeat_interval, request_timeout
 * - log_level, log_dir
 *
 * Environment variables (.env):
 * - ENV (determines which YAML to load: development, production, test)
 * - PASSEUR_SOLANA_RPC_URL (required)
 * - PASSEUR_PROGRAM_ID (required)
 * - PASSEUR_SOLANA_NETWORK (required)
 * - PASSEUR_PLATFORM_KEYPAIR_PATH (required, sensitive)
 */
function loadConfig() {
  // Determine environment
  const env = process.env.ENV || 'production';

  // Map environment to config file
  const configMap = {
    'production': 'production.yaml',
    'development': 'development.yaml',
    'test': 'test.yaml',
  };

  // Load default config first
  const defaultConfigPath = path.join(__dirname, '../config', 'default.yaml');
  let config = {};

  if (fs.existsSync(defaultConfigPath)) {
    config = yaml.load(fs.readFileSync(defaultConfigPath, 'utf8')) || {};
    console.log('[CONFIG] Loaded default.yaml');
  }

  // Load environment-specific config (overrides defaults)
  const envConfigFile = configMap[env] || 'production.yaml';
  const envConfigPath = path.join(__dirname, '../config', envConfigFile);

  if (fs.existsSync(envConfigPath)) {
    const envConfig = yaml.load(fs.readFileSync(envConfigPath, 'utf8')) || {};
    config = { ...config, ...envConfig };
    console.log(`[CONFIG] Loaded ${envConfigFile}`);
  } else {
    console.warn(`[CONFIG] Config file not found: ${envConfigPath}`);
  }

  // Required environment variables
  const requiredEnvVars = [
    'PASSEUR_SOLANA_RPC_URL',
    'PASSEUR_PROGRAM_ID',
    'PASSEUR_SOLANA_NETWORK',
    'PASSEUR_PLATFORM_KEYPAIR_PATH',
  ];

  const missing = requiredEnvVars.filter(v => !process.env[v]);
  if (missing.length > 0) {
    console.error('[CONFIG] Missing required environment variables:');
    missing.forEach(v => console.error(`  - ${v}`));
    console.error('[CONFIG] Tip: Create a .env file with these variables');
    process.exit(1);
  }

  // Merge config: ENV overrides YAML
  const finalConfig = {
    // From YAML or defaults (non-sensitive)
    bridge_host: config.bridge_host || '0.0.0.0',
    bridge_port: config.bridge_port || 8766,
    heartbeat_interval: config.heartbeat_interval || 30,
    request_timeout: config.request_timeout || 30,
    log_level: config.log_level || 'info',
    log_dir: config.log_dir || 'logs',

    // From ENV (required, sensitive or changeable)
    solana_rpc_url: process.env.PASSEUR_SOLANA_RPC_URL,
    program_id: process.env.PASSEUR_PROGRAM_ID,
    solana_network: process.env.PASSEUR_SOLANA_NETWORK,
    platform_keypair_path: process.env.PASSEUR_PLATFORM_KEYPAIR_PATH,
  };

  console.log(`[CONFIG] Environment: ${env}`);
  console.log('[CONFIG] Configuration loaded (default + env-specific + ENV)');
  return finalConfig;
}

const CONFIG = loadConfig();

// Expand home directory in keypair path
const PLATFORM_KEYPAIR_PATH = CONFIG.platform_keypair_path.replace(
  '~',
  process.env.HOME || '/root'
);

// ============================================================
// INITIALIZATION
// ============================================================

let platformKeypair;
try {
  const keypairData = JSON.parse(
    fs.readFileSync(PLATFORM_KEYPAIR_PATH, 'utf8')
  );
  platformKeypair = Keypair.fromSecretKey(Uint8Array.from(keypairData));
  console.log(`[INIT] Platform wallet: ${platformKeypair.publicKey.toString()}`);
} catch (error) {
  console.error(`[INIT] Failed to load platform keypair: ${error.message}`);
  process.exit(1);
}

const connection = new Connection(CONFIG.solana_rpc_url, 'confirmed');
const programId = new PublicKey(CONFIG.program_id);

console.log(`[INIT] Program ID: ${programId.toString()}`);

(async () => {
  try {
    const version = await connection.getVersion();
    console.log(`[INIT] Connected to: ${CONFIG.solana_network}`);
    console.log(`[INIT] RPC: ${CONFIG.solana_rpc_url}`);
    console.log(`[INIT] Solana version: ${version['solana-core']}`);
  } catch (error) {
    console.error(`[INIT] Failed to connect to Solana: ${error.message}`);
    process.exit(1);
  }
})();

// ============================================================
// HELPER FUNCTIONS
// ============================================================

/**
 * Fetch and deserialize escrow account data.
 *
 * @param {PublicKey} escrowAddress - Escrow account address
 * @returns {Object} Deserialized escrow account data
 */
async function fetchEscrowAccount(escrowAddress) {
  const accountInfo = await connection.getAccountInfo(escrowAddress);

  if (!accountInfo) {
    throw new Error('Escrow account not found');
  }

  const data = accountInfo.data;
  let offset = 8; // Skip discriminator

  // Deserialize account fields
  const user = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;

  const platformAuthority = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;

  const tradingAuthority = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;

  const tokenMint = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;

  const bump = data[offset];
  offset += 1;

  const flags = data[offset];
  offset += 1;

  const createdAt = data.readBigInt64LE(offset);
  offset += 8;

  const platformActivatedAt = data.readBigInt64LE(offset);
  offset += 8;

  const tradingActivatedAt = data.readBigInt64LE(offset);
  offset += 8;

  const lastPausedAt = data.readBigInt64LE(offset);
  offset += 8;

  const actionNonce = data.readBigUInt64LE(offset);
  offset += 8;

  const totalDeposited = data.readBigUInt64LE(offset);
  offset += 8;

  const totalWithdrawn = data.readBigUInt64LE(offset);
  offset += 8;

  const totalFeesPaid = data.readBigUInt64LE(offset);
  offset += 8;

  const totalTraded = data.readBigUInt64LE(offset);
  offset += 8;

  const maxBalance = data.readBigUInt64LE(offset);
  offset += 8;

  const maxLifetime = data.readBigInt64LE(offset);
  offset += 8;

  const reserved = data.slice(offset, offset + 176);

  return {
    discriminator: data.slice(0, 8),
    user,
    platformAuthority,
    tradingAuthority,
    tokenMint,
    bump,
    flags,
    createdAt,
    platformActivatedAt,
    tradingActivatedAt,
    lastPausedAt,
    actionNonce,
    totalDeposited,
    totalWithdrawn,
    totalFeesPaid,
    totalTraded,
    maxBalance,
    maxLifetime,
    reserved,
  };
}

// ============================================================
// EXPRESS APP
// ============================================================

const app = express();
app.use(express.json());

// ============================================================
// HEALTH & INFO
// ============================================================

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    network: CONFIG.solana_network,
    program: programId.toString(),
    wallet: platformKeypair.publicKey.toString(),
    timestamp: new Date().toISOString(),
  });
});

// ============================================================
// WALLET BALANCE ENDPOINT
// ============================================================

app.get('/wallet/balance', async (req, res) => {
  try {
    const { wallet } = req.query;

    if (!wallet) {
      return res.status(400).json({
        success: false,
        error: 'Missing wallet parameter',
      });
    }

    const walletPubkey = new PublicKey(wallet);

    // USDC devnet token mint
    const tokenMint = new PublicKey(
      '4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU'
    );

    // Get associated token account for wallet
    const userTokenAccount = await getAssociatedTokenAddress(
      tokenMint,
      walletPubkey
    );

    // Get token balance
    const tokenInfo = await connection.getTokenAccountBalance(
      userTokenAccount
    );

    console.log(
      `[BALANCE] Wallet balance: ${walletPubkey.toString().slice(0, 8)}... = ${
        tokenInfo.value.uiAmount
      } USDC`
    );

    res.json({
      success: true,
      balance: tokenInfo.value.uiAmount,
      balanceLamports: tokenInfo.value.amount,
      decimals: tokenInfo.value.decimals,
      tokenMint: tokenMint.toString(),
      wallet: walletPubkey.toString(),
    });
  } catch (error) {
    console.error('[BALANCE] Get wallet balance error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================
// PREPARE TRANSACTION ENDPOINTS
// ============================================================

app.post('/escrow/prepare-initialize', async (req, res) => {
  try {
    const { userWallet, maxBalance } = req.body;

    if (!userWallet) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet',
      });
    }

    const userPubkey = new PublicKey(userWallet);

    // Derive PDA (user-only seeds, NO strategy_id)
    const [escrowPDA, bump] = PublicKey.findProgramAddressSync(
      [Buffer.from('escrow'), userPubkey.toBuffer()],
      programId
    );

    const tokenMint = new PublicKey(
      '4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU'
    );

    const escrowTokenAccount = await getAssociatedTokenAddress(
      tokenMint,
      escrowPDA,
      true
    );

    const ix = buildInitializeEscrowInstruction({
      escrow: escrowPDA,
      escrowTokenAccount,
      tokenMint,
      user: userPubkey,
      programId,
      bump: bump,
      maxBalance: maxBalance ? BigInt(maxBalance) : BigInt(0),
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log(
      `[PREPARE] Initialize: ${userPubkey.toString().slice(0, 8)}...`
    );
    console.log(`[PREPARE] Escrow: ${escrowPDA.toString().slice(0, 8)}...`);

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      escrowAccount: escrowPDA.toString(),
      bump: bump,
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Initialize error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-delegate-platform', async (req, res) => {
  try {
    const { userWallet, escrowAccount, authority } = req.body;

    if (!userWallet || !escrowAccount || !authority) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet, escrowAccount or authority',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);
    const authorityPubkey = new PublicKey(authority);

    const ix = buildDelegatePlatformAuthorityInstruction({
      escrow: escrowPDA,
      user: userPubkey,
      authority: authorityPubkey,
      programId,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log(
      `[PREPARE] Delegate platform: ${authorityPubkey
        .toString()
        .slice(0, 8)}...`
    );

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Delegate platform error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-delegate-trading', async (req, res) => {
  try {
    const { userWallet, escrowAccount, authority } = req.body;

    if (!userWallet || !escrowAccount || !authority) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet, escrowAccount or authority',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);
    const authorityPubkey = new PublicKey(authority);

    const ix = buildDelegateTradingAuthorityInstruction({
      escrow: escrowPDA,
      user: userPubkey,
      authority: authorityPubkey,
      programId,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log(
      `[PREPARE] Delegate trading: ${authorityPubkey
        .toString()
        .slice(0, 8)}...`
    );

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Delegate trading error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-revoke-platform', async (req, res) => {
  try {
    const { userWallet, escrowAccount } = req.body;

    if (!userWallet || !escrowAccount) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet or escrowAccount',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);

    const ix = buildRevokePlatformAuthorityInstruction({
      escrow: escrowPDA,
      user: userPubkey,
      programId,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log('[PREPARE] Revoke platform authority');

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Revoke platform error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-revoke-trading', async (req, res) => {
  try {
    const { userWallet, escrowAccount } = req.body;

    if (!userWallet || !escrowAccount) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet or escrowAccount',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);

    const ix = buildRevokeTradingAuthorityInstruction({
      escrow: escrowPDA,
      user: userPubkey,
      programId,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log('[PREPARE] Revoke trading authority');

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Revoke trading error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-deposit', async (req, res) => {
  try {
    const { userWallet, escrowAccount, amount } = req.body;

    if (!userWallet || !escrowAccount || !amount) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet, escrowAccount or amount',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);

    const escrowData = await fetchEscrowAccount(escrowPDA);

    const userTokenAccount = await getAssociatedTokenAddress(
      escrowData.tokenMint,
      userPubkey
    );

    const escrowTokenAccount = await getAssociatedTokenAddress(
      escrowData.tokenMint,
      escrowPDA,
      true
    );

    const depositAmount = BigInt(Math.floor(parseFloat(amount) * 1_000_000));

    const discriminator = DISCRIMINATORS.DEPOSIT;
    const amountBuffer = Buffer.alloc(8);
    amountBuffer.writeBigUInt64LE(depositAmount);
    const data = Buffer.concat([discriminator, amountBuffer]);

    const keys = [
      { pubkey: escrowPDA, isSigner: false, isWritable: true },
      { pubkey: escrowTokenAccount, isSigner: false, isWritable: true },
      { pubkey: userTokenAccount, isSigner: false, isWritable: true },
      { pubkey: escrowData.tokenMint, isSigner: false, isWritable: false },
      { pubkey: userPubkey, isSigner: true, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ];

    const ix = new TransactionInstruction({
      keys,
      programId,
      data,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log(`[PREPARE] Deposit: ${amount} USDC`);

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      amount: depositAmount.toString(),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Deposit error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-withdraw', async (req, res) => {
  try {
    const { userWallet, escrowAccount, amount } = req.body;

    if (!userWallet || !escrowAccount) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet or escrowAccount',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);

    const escrowData = await fetchEscrowAccount(escrowPDA);

    const userTokenAccount = await getAssociatedTokenAddress(
      escrowData.tokenMint,
      userPubkey
    );

    const escrowTokenAccount = await getAssociatedTokenAddress(
      escrowData.tokenMint,
      escrowPDA,
      true
    );

    const escrowTokenInfo = await connection.getTokenAccountBalance(
      escrowTokenAccount
    );
    const currentBalance = BigInt(escrowTokenInfo.value.amount);

    const withdrawAmount = amount
      ? BigInt(Math.floor(parseFloat(amount) * 1_000_000))
      : currentBalance;

    const ix = buildWithdrawInstruction({
      escrow: escrowPDA,
      escrowTokenAccount,
      userTokenAccount,
      tokenMint: escrowData.tokenMint,
      user: userPubkey,
      programId,
      amount: withdrawAmount,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log(`[PREPARE] Withdraw: ${withdrawAmount} tokens`);

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      amount: withdrawAmount.toString(),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Withdraw error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.post('/escrow/prepare-close', async (req, res) => {
  try {
    const { userWallet, escrowAccount } = req.body;

    if (!userWallet || !escrowAccount) {
      return res.status(400).json({
        success: false,
        error: 'Missing userWallet or escrowAccount',
      });
    }

    const userPubkey = new PublicKey(userWallet);
    const escrowPDA = new PublicKey(escrowAccount);

    const escrowData = await fetchEscrowAccount(escrowPDA);

    const escrowTokenAccount = await getAssociatedTokenAddress(
      escrowData.tokenMint,
      escrowPDA,
      true
    );

    const ix = buildCloseEscrowInstruction({
      escrow: escrowPDA,
      escrowTokenAccount,
      user: userPubkey,
      programId,
    });

    const { blockhash } = await connection.getLatestBlockhash();

    const transaction = new Transaction();
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = userPubkey;
    transaction.add(ix);

    const serialized = transaction.serialize({
      requireAllSignatures: false,
      verifySignatures: false,
    });

    console.log('[PREPARE] Close escrow');

    res.json({
      success: true,
      transaction: serialized.toString('base64'),
      message: 'Transaction ready for signing',
    });
  } catch (error) {
    console.error('[PREPARE] Close error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================
// TRANSACTION SUBMISSION (Generic endpoint)
// ============================================================

app.post('/transaction/submit', async (req, res) => {
  try {
    const { signedTransaction } = req.body;

    if (!signedTransaction) {
      return res.status(400).json({
        success: false,
        error: 'Missing signedTransaction',
      });
    }

    const txBuffer = Buffer.from(signedTransaction, 'base64');
    const tx = Transaction.from(txBuffer);

    const signature = await connection.sendRawTransaction(tx.serialize(), {
      skipPreflight: false,
      preflightCommitment: 'confirmed',
    });

    console.log(`[TX] Transaction submitted: ${signature.slice(0, 8)}...`);

    res.json({
      success: true,
      signature: signature,
    });
  } catch (error) {
    console.error('[TX] Submit transaction error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================
// QUERY ENDPOINTS
// ============================================================

app.get('/escrow/:address', async (req, res) => {
  try {
    const escrowAddress = new PublicKey(req.params.address);
    const escrowAccount = await fetchEscrowAccount(escrowAddress);

    res.json({
      success: true,
      data: {
        address: escrowAddress.toString(),
        user: escrowAccount.user.toString(),
        platformAuthority: escrowAccount.platformAuthority.toString(),
        tradingAuthority: escrowAccount.tradingAuthority.toString(),
        tokenMint: escrowAccount.tokenMint.toString(),
        bump: escrowAccount.bump,
        isPlatformActive: (escrowAccount.flags & 0b0001) !== 0,
        isTradingActive: (escrowAccount.flags & 0b0010) !== 0,
        isPaused: (escrowAccount.flags & 0b0100) !== 0,
        createdAt: escrowAccount.createdAt.toString(),
        platformActivatedAt: escrowAccount.platformActivatedAt.toString(),
        tradingActivatedAt: escrowAccount.tradingActivatedAt.toString(),
        lastPausedAt: escrowAccount.lastPausedAt.toString(),
        actionNonce: escrowAccount.actionNonce.toString(),
        totalDeposited: escrowAccount.totalDeposited.toString(),
        totalWithdrawn: escrowAccount.totalWithdrawn.toString(),
        totalFeesPaid: escrowAccount.totalFeesPaid.toString(),
        totalTraded: escrowAccount.totalTraded.toString(),
        maxBalance: escrowAccount.maxBalance.toString(),
        maxLifetime: escrowAccount.maxLifetime.toString(),
      },
    });
  } catch (error) {
    console.error('[QUERY] Get escrow details error:', error);
    res.status(404).json({
      success: false,
      error: error.message,
    });
  }
});

app.get('/escrow/balance/:account', async (req, res) => {
  try {
    const escrowPDA = new PublicKey(req.params.account);
    const escrowData = await fetchEscrowAccount(escrowPDA);

    const escrowTokenAccount = await getAssociatedTokenAddress(
      escrowData.tokenMint,
      escrowPDA,
      true
    );

    const tokenInfo = await connection.getTokenAccountBalance(
      escrowTokenAccount
    );

    res.json({
      success: true,
      balance: tokenInfo.value.uiAmount,
      balanceLamports: tokenInfo.value.amount,
      decimals: tokenInfo.value.decimals,
      tokenMint: escrowData.tokenMint.toString(),
    });
  } catch (error) {
    console.error('[QUERY] Get balance error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

app.get('/transaction/status/:signature', async (req, res) => {
  try {
    const signature = req.params.signature;

    // Validate signature format
    if (!signature || signature.length < 87 || signature.length > 88) {
      return res.json({
        success: true,
        confirmed: false,
        status: 'invalid_signature',
      });
    }

    const base58Regex = /^[1-9A-HJ-NP-Za-km-z]+$/;
    if (!base58Regex.test(signature)) {
      return res.json({
        success: true,
        confirmed: false,
        status: 'invalid_signature',
      });
    }

    const status = await connection.getSignatureStatus(signature);

    if (status.value === null) {
      return res.json({
        success: true,
        confirmed: false,
        status: 'not_found',
      });
    }

    res.json({
      success: true,
      confirmed: status.value.confirmationStatus === 'finalized',
      confirmationStatus: status.value.confirmationStatus,
      slot: status.value.slot,
      err: status.value.err,
    });
  } catch (error) {
    if (error.message && error.message.includes('Invalid')) {
      return res.json({
        success: true,
        confirmed: false,
        status: 'invalid_signature',
      });
    }

    console.error('[QUERY] Transaction status error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
});

// ============================================================
// WEBSOCKET SERVER
// ============================================================

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  console.log('[WS] New WebSocket connection');

  ws.isAlive = true;
  ws.on('pong', () => {
    ws.isAlive = true;
  });

  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);

      switch (data.type) {
        case 'subscribe':
          if (data.escrow) {
            ws.send(
              JSON.stringify({
                type: 'subscribed',
                escrow: data.escrow,
              })
            );
          }
          break;

        case 'ping':
          ws.send(JSON.stringify({ type: 'pong' }));
          break;

        default:
          ws.send(
            JSON.stringify({
              type: 'error',
              message: 'Unknown message type',
            })
          );
      }
    } catch (error) {
      ws.send(
        JSON.stringify({
          type: 'error',
          message: error.message,
        })
      );
    }
  });

  ws.on('close', () => {
    console.log('[WS] WebSocket closed');
  });
});

// Heartbeat to detect broken connections
const heartbeat = setInterval(() => {
  wss.clients.forEach((ws) => {
    if (ws.isAlive === false) {
      return ws.terminate();
    }
    ws.isAlive = false;
    ws.ping();
  });
}, CONFIG.heartbeat_interval * 1000);

wss.on('close', () => {
  clearInterval(heartbeat);
});

// ============================================================
// START SERVER
// ============================================================

server.listen(CONFIG.bridge_port, CONFIG.bridge_host, () => {
  console.log('='.repeat(60));
  console.log('PASSEUR BRIDGE (User-Based Escrow)');
  console.log('='.repeat(60));
  console.log(`HTTP: http://${CONFIG.bridge_host}:${CONFIG.bridge_port}`);
  console.log(`WebSocket: ws://${CONFIG.bridge_host}:${CONFIG.bridge_port}`);
  console.log(`Network: ${CONFIG.solana_network}`);
  console.log(`Program: ${programId.toString()}`);
  console.log('='.repeat(60));
});

process.on('SIGINT', () => {
  console.log('\n[SERVER] Shutting down...');
  server.close(() => {
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('\n[SERVER] Shutting down...');
  server.close(() => {
    process.exit(0);
  });
});

module.exports = { app, server, connection };
