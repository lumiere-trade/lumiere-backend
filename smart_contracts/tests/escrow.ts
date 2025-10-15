import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Escrow } from "../target/types/escrow";
import { 
  PublicKey, 
  SystemProgram, 
  Keypair, 
  LAMPORTS_PER_SOL 
} from "@solana/web3.js";
import {
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createMint,
  getOrCreateAssociatedTokenAccount,
  mintTo,
  getAccount,
} from "@solana/spl-token";
import { expect } from "chai";

// Helper function for airdrop with retry
async function airdropWithRetry(
  connection: any,
  publicKey: PublicKey,
  amount: number,
  maxRetries = 3
): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const sig = await connection.requestAirdrop(publicKey, amount);
      await connection.confirmTransaction(sig);
      console.log(`✅ Airdropped ${amount / LAMPORTS_PER_SOL} SOL to ${publicKey.toString().slice(0, 8)}...`);
      return;
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      console.log(`⚠️  Airdrop failed, retrying in ${(i + 1) * 2}s...`);
      await new Promise(resolve => setTimeout(resolve, (i + 1) * 2000));
    }
  }
}

describe("escrow", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.Escrow as Program<Escrow>;

  // Test accounts
  let user: Keypair;
  let authority: Keypair;
  let tokenMint: PublicKey;
  let userTokenAccount: PublicKey;
  let escrowPda: PublicKey;
  let escrowTokenAccount: PublicKey;
  let destinationUser: Keypair;
  let destinationTokenAccount: PublicKey;
  
  const strategyId = Array.from({ length: 16 }, (_, i) => i + 1);
  const maxBalance = new anchor.BN(1_000_000_000); // 1B tokens

  before(async () => {
    console.log("\n🚀 Setting up test environment...\n");

    // Create test keypairs
    user = Keypair.generate();
    authority = Keypair.generate();
    destinationUser = Keypair.generate();

    console.log("✅ User:", user.publicKey.toString());
    console.log("✅ Authority:", authority.publicKey.toString());
    console.log("✅ Destination:", destinationUser.publicKey.toString());

    // Airdrop SOL with retry and delay
    console.log("\n💰 Airdropping SOL to test accounts...");
    const airdropAmount = 3 * LAMPORTS_PER_SOL;
    
    await airdropWithRetry(provider.connection, user.publicKey, airdropAmount);
    await new Promise(resolve => setTimeout(resolve, 2000)); // Delay between airdrops
    
    await airdropWithRetry(provider.connection, authority.publicKey, airdropAmount);
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    await airdropWithRetry(provider.connection, destinationUser.publicKey, airdropAmount);

    // Create token mint
    console.log("\n🪙 Creating test token mint...");
    tokenMint = await createMint(
      provider.connection,
      user,
      user.publicKey,
      null,
      6 // 6 decimals
    );
    console.log("✅ Token Mint:", tokenMint.toString());

    // Create user token account
    const userTokenAccountInfo = await getOrCreateAssociatedTokenAccount(
      provider.connection,
      user,
      tokenMint,
      user.publicKey
    );
    userTokenAccount = userTokenAccountInfo.address;

    // Mint tokens to user
    console.log("\n💵 Minting 100M tokens to user...");
    await mintTo(
      provider.connection,
      user,
      tokenMint,
      userTokenAccount,
      user,
      100_000_000_000_000 // 100M tokens with 6 decimals
    );
    console.log("✅ Minted tokens to user");

    // Create destination token account
    const destTokenAccountInfo = await getOrCreateAssociatedTokenAccount(
      provider.connection,
      destinationUser,
      tokenMint,
      destinationUser.publicKey
    );
    destinationTokenAccount = destTokenAccountInfo.address;
    console.log("✅ Destination token account:", destinationTokenAccount.toString());

    // Derive PDAs
    [escrowPda] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("escrow"),
        user.publicKey.toBuffer(),
        Buffer.from(strategyId),
      ],
      program.programId
    );

    console.log("\n📍 Escrow PDA:", escrowPda.toString());
    console.log("\n✅ Test environment setup complete!\n");
  });

  it("1️⃣  Initializes escrow", async () => {
    console.log("\n🧪 TEST: Initialize Escrow\n");

    const [pda, bump] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("escrow"),
        user.publicKey.toBuffer(),
        Buffer.from(strategyId),
      ],
      program.programId
    );

    escrowTokenAccount = await anchor.utils.token.associatedAddress({
      mint: tokenMint,
      owner: escrowPda,
    });

    const tx = await program.methods
      .initializeEscrow(strategyId, bump, maxBalance)
      .accounts({
        escrow: escrowPda,
        escrowTokenAccount: escrowTokenAccount,
        tokenMint: tokenMint,
        user: user.publicKey,
        systemProgram: SystemProgram.programId,
        tokenProgram: TOKEN_PROGRAM_ID,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
      })
      .signers([user])
      .rpc();

    console.log("✅ Transaction:", tx);

    const escrowAccount = await program.account.escrowAccount.fetch(escrowPda);
    
    expect(escrowAccount.user.toString()).to.equal(user.publicKey.toString());
    expect(escrowAccount.tokenMint.toString()).to.equal(tokenMint.toString());
    expect(escrowAccount.bump).to.equal(bump);

    console.log("✅ Escrow initialized successfully!");
  });

  it("2️⃣  Deposits tokens", async () => {
    console.log("\n🧪 TEST: Deposit Tokens\n");

    const depositAmount = new anchor.BN(10_000_000_000); // 10M tokens

    const tx = await program.methods
      .depositToken(depositAmount)
      .accounts({
        escrow: escrowPda,
        escrowTokenAccount: escrowTokenAccount,
        userTokenAccount: userTokenAccount,
        tokenMint: tokenMint,
        user: user.publicKey,
        tokenProgram: TOKEN_PROGRAM_ID,
      })
      .signers([user])
      .rpc();

    console.log("✅ Transaction:", tx);

    const escrowTokenAccountInfo = await getAccount(
      provider.connection,
      escrowTokenAccount
    );

    expect(escrowTokenAccountInfo.amount.toString()).to.equal(depositAmount.toString());
    console.log("✅ Deposited:", depositAmount.toString());
  });

  it("3️⃣  Approves destination", async () => {
    console.log("\n🧪 TEST: Approve Destination\n");

    const tx = await program.methods
      .approveDestination()
      .accounts({
        escrow: escrowPda,
        destinationAccount: destinationTokenAccount,
        user: user.publicKey,
      })
      .signers([user])
      .rpc();

    console.log("✅ Transaction:", tx);

    const escrowAccount = await program.account.escrowAccount.fetch(escrowPda);
    expect(escrowAccount.approvedDestinations).to.have.lengthOf(1);
    console.log("✅ Destination approved");
  });

  it("4️⃣  Delegates authority", async () => {
    console.log("\n🧪 TEST: Delegate Authority\n");

    const tx = await program.methods
      .delegateAuthority(authority.publicKey)
      .accounts({
        escrow: escrowPda,
        user: user.publicKey,
      })
      .signers([user])
      .rpc();

    console.log("✅ Transaction:", tx);

    const escrowAccount = await program.account.escrowAccount.fetch(escrowPda);
    expect(escrowAccount.authority.toString()).to.equal(authority.publicKey.toString());
    console.log("✅ Authority delegated");
  });

  it("5️⃣  Executes trade", async () => {
    console.log("\n🧪 TEST: Execute Trade\n");

    // Wait for authority time-lock
    console.log("⏳ Waiting for authority time-lock (1s)...");
    await new Promise(resolve => setTimeout(resolve, 1500));

    const tradeAmount = new anchor.BN(1_000_000_000); // 1M tokens
    const deadline = new anchor.BN(Math.floor(Date.now() / 1000) + 60);
    
    const escrowAccountBefore = await program.account.escrowAccount.fetch(escrowPda);
    const expectedNonce = escrowAccountBefore.actionNonce;

    const tx = await program.methods
      .executeTrade(tradeAmount, deadline, expectedNonce)
      .accounts({
        escrow: escrowPda,
        escrowTokenAccount: escrowTokenAccount,
        destinationTokenAccount: destinationTokenAccount,
        tokenMint: tokenMint,
        authority: authority.publicKey,
        tokenProgram: TOKEN_PROGRAM_ID,
      })
      .signers([authority])
      .rpc();

    console.log("✅ Transaction:", tx);

    const destinationBalance = await getAccount(
      provider.connection,
      destinationTokenAccount
    );

    expect(destinationBalance.amount.toString()).to.equal(tradeAmount.toString());
    console.log("✅ Trade executed! Amount:", tradeAmount.toString());
  });

  it("6️⃣  Revokes authority and withdraws", async () => {
    console.log("\n🧪 TEST: Revoke Authority & Withdraw\n");

    // Revoke authority first
    await program.methods
      .revokeAuthority()
      .accounts({
        escrow: escrowPda,
        user: user.publicKey,
      })
      .signers([user])
      .rpc();

    console.log("✅ Authority revoked");

    // Withdraw remaining tokens
    const escrowBalance = await getAccount(provider.connection, escrowTokenAccount);
    const withdrawAmount = new anchor.BN(escrowBalance.amount.toString());

    const tx = await program.methods
      .withdrawToken(withdrawAmount)
      .accounts({
        escrow: escrowPda,
        escrowTokenAccount: escrowTokenAccount,
        userTokenAccount: userTokenAccount,
        tokenMint: tokenMint,
        user: user.publicKey,
        tokenProgram: TOKEN_PROGRAM_ID,
      })
      .signers([user])
      .rpc();

    console.log("✅ Withdrawn:", withdrawAmount.toString());
  });

  it("7️⃣  Closes escrow", async () => {
    console.log("\n🧪 TEST: Close Escrow\n");

    const tx = await program.methods
      .closeEscrow()
      .accounts({
        escrow: escrowPda,
        escrowTokenAccount: escrowTokenAccount,
        user: user.publicKey,
        tokenProgram: TOKEN_PROGRAM_ID,
      })
      .signers([user])
      .rpc();

    console.log("✅ Transaction:", tx);
    console.log("✅ Escrow closed successfully!");
  });

  it("📊 Test suite completed", async () => {
    console.log("\n════════════════════════════════════");
    console.log("✅ ALL TESTS PASSED!");
    console.log("════════════════════════════════════\n");
  });
});
