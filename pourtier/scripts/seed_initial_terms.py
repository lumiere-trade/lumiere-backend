"""
Seed initial Terms of Service document.

Creates the first version of Terms of Service for Lumiere platform.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pourtier.domain.entities.legal_document import (
    DocumentStatus,
    DocumentType,
    LegalDocument,
)
from pourtier.infrastructure.persistence.database import (
    Database,
)
from pourtier.infrastructure.persistence.repositories.legal_document_repository import (
    LegalDocumentRepository,
)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Get DATABASE_URL from environment (Docker provides this)
DATABASE_URL = os.getenv("DATABASE_URL")

TERMS_OF_SERVICE_CONTENT = """
LUMIERE TRADING SYSTEM - TERMS OF SERVICE

Effective Date: October 21, 2025
Version: 1.0.0


1. ACCEPTANCE OF TERMS

By accessing or using the Lumiere Trading System (the "Platform"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Platform.


2. DESCRIPTION OF SERVICE

Lumiere is a decentralized finance (DeFi) trading platform that provides:

  • AI-assisted strategy creation tools
  • Automated trading execution on blockchain networks
  • Market analysis and historical data visualization
  • Real-time performance monitoring


3. RISK DISCLOSURE AND DISCLAIMERS

3.1 Trading Risks

YOU ACKNOWLEDGE AND ACCEPT THE FOLLOWING RISKS:

  • High Volatility: Cryptocurrency markets are highly volatile. Prices can change rapidly and unpredictably.

  • Total Loss: You may lose all funds allocated to trading strategies. Never invest more than you can afford to lose.

  • No Guarantees: Past performance does not guarantee future results. Backtested strategies may not perform as expected in live markets.

  • Market Conditions: Strategies may fail during extreme market conditions, low liquidity, or high volatility.

  • Smart Contract Risk: Blockchain transactions are irreversible. Smart contract bugs or exploits may result in loss of funds.


3.2 No Financial Advice

THE PLATFORM DOES NOT PROVIDE FINANCIAL, INVESTMENT, OR TRADING ADVICE.

  • All tools, analyses, and AI-generated content are for informational purposes only.
  • The Platform does not recommend, endorse, or suggest any specific trading strategy.
  • You are solely responsible for your trading decisions.
  • Consult qualified financial advisors before making investment decisions.


3.3 AI-Generated Content

AI components (Prophet, Architect) provide suggestions, not recommendations:

  • AI-generated strategies are experimental and unproven.
  • AI cannot predict market movements or guarantee profits.
  • Users must review, understand, and validate all AI suggestions before use.
  • The Platform is not liable for losses from AI-generated strategies.


3.4 Automated Trading Risks

Automated trading carries additional risks:

  • Execution Risk: Orders may fail, be delayed, or execute at unfavorable prices.
  • System Failures: Technical issues, bugs, or outages may prevent strategy execution.
  • Parameter Errors: Incorrect strategy parameters may result in unexpected behavior.
  • Slippage: Actual execution prices may differ from expected prices.


4. USER RESPONSIBILITIES

You are responsible for:

  • Security: Safeguarding your wallet private keys and seed phrases.
  • Funds: Managing your escrow account and trading capital.
  • Strategies: Understanding, testing, and monitoring your trading strategies.
  • Compliance: Adhering to applicable laws and regulations in your jurisdiction.
  • Due Diligence: Researching and understanding the risks before trading.


5. PLATFORM LIMITATIONS

5.1 No Liability for Losses

THE PLATFORM IS NOT LIABLE FOR:

  • Trading losses or investment performance
  • Failed transactions or missed opportunities
  • Smart contract vulnerabilities or exploits
  • Third-party service failures (RPC nodes, oracles, etc.)
  • Market manipulation or flash crashes
  • User errors or misconfigurations


5.2 Service Availability

  • The Platform is provided "AS IS" without warranties.
  • We do not guarantee uninterrupted or error-free service.
  • Maintenance, updates, or technical issues may cause downtime.
  • We reserve the right to modify or discontinue features.


5.3 Data Accuracy

  • Market data, analyses, and indicators are provided for reference.
  • We do not guarantee accuracy, completeness, or timeliness of data.
  • Users should verify critical information independently.


6. PROHIBITED ACTIVITIES

You may NOT:

  • Use the Platform for illegal activities or fraud
  • Attempt to manipulate markets or engage in wash trading
  • Exploit bugs or vulnerabilities for personal gain
  • Reverse engineer, decompile, or hack the Platform
  • Use the Platform to harm other users or the ecosystem
  • Create accounts using false or misleading information


7. ESCROW AND FUNDS MANAGEMENT

7.1 Escrow Accounts

  • Users deposit funds to personal escrow accounts (Solana PDAs).
  • The Platform facilitates escrow creation but does NOT custody your funds.
  • You retain control via your wallet's private keys.


7.2 Withdrawals

  • You may withdraw funds at any time (subject to blockchain confirmation).
  • Withdrawals are final and irreversible.
  • Ensure recipient addresses are correct before confirming.


7.3 Fees

  • Blockchain transaction fees (gas) apply to all operations.
  • Platform service fees (if any) will be disclosed transparently.
  • Third-party fees (DEX spreads, slippage) are beyond our control.


8. INTELLECTUAL PROPERTY

  • The Platform's code, design, and content are proprietary.
  • User-generated strategies remain the user's intellectual property.
  • By using the Platform, you grant us a license to operate your strategies (execution only, not commercial use).


9. PRIVACY AND DATA

  • We collect minimal data necessary for Platform operation.
  • Wallet addresses and transaction signatures are recorded for audit purposes.
  • We do NOT sell or share user data with third parties.
  • See our Privacy Policy for details.


10. TERMINATION

  • You may stop using the Platform at any time.
  • We reserve the right to terminate accounts violating these Terms.
  • Upon termination, you must withdraw funds from escrow promptly.


11. AMENDMENTS

  • We may update these Terms periodically.
  • Changes will be communicated via the Platform.
  • Continued use after changes constitutes acceptance.


12. GOVERNING LAW AND DISPUTES

  • These Terms are governed by the laws of [JURISDICTION TBD].
  • Disputes will be resolved through binding arbitration.
  • You waive the right to class action lawsuits.


13. LIMITATION OF LIABILITY

TO THE MAXIMUM EXTENT PERMITTED BY LAW:

  • The Platform and its operators are NOT LIABLE for any direct, indirect, incidental, consequential, or punitive damages.
  • This includes but is not limited to: trading losses, lost profits, data loss, system failures, or unauthorized access.
  • Total liability (if any) is limited to fees paid in the past 12 months.


14. INDEMNIFICATION

You agree to indemnify and hold harmless the Platform, its operators, and affiliates from any claims, damages, or expenses arising from:

  • Your use of the Platform
  • Your violation of these Terms
  • Your trading activities and strategies
  • Your breach of applicable laws


15. SEVERABILITY

If any provision of these Terms is found invalid or unenforceable, the remaining provisions remain in full effect.


16. CONTACT INFORMATION

For questions or concerns regarding these Terms:

  • Email: legal@lumiere.trade
  • Platform: https://lumiere.trade/support


────────────────────────────────────────────────────────────

BY USING THE LUMIERE PLATFORM, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREED TO THESE TERMS OF SERVICE.

YOU UNDERSTAND THE RISKS OF CRYPTOCURRENCY TRADING AND ACCEPT FULL RESPONSIBILITY FOR YOUR TRADING DECISIONS AND OUTCOMES.

TRADE AT YOUR OWN RISK.

────────────────────────────────────────────────────────────

Last Updated: October 21, 2025
Version: 1.0.0
""".strip()


async def seed_initial_terms():
    """Create initial Terms of Service document."""
    print("Seeding Initial Terms of Service")
    print("=" * 50)

    database = Database(
        database_url=DATABASE_URL,
        echo=False,
    )

    try:
        await database.connect()
        print("Connected to database")

        async with database.session() as session:
            repo = LegalDocumentRepository(session)
            existing = await repo.get_active_by_type(DocumentType.TERMS_OF_SERVICE)

            if existing:
                print("Terms of Service already exist!")
                print(f"   ID: {existing.id}")
                print(f"   Version: {existing.version}")
                print(f"   Status: {existing.status.value}")
                print("\nSkipping seed (document already exists)")
                return

            now = datetime.now()

            terms = LegalDocument(
                id=uuid4(),
                document_type=DocumentType.TERMS_OF_SERVICE,
                version="1.0.0",
                title="Lumiere Trading System - Terms of Service",
                content=TERMS_OF_SERVICE_CONTENT,
                status=DocumentStatus.ACTIVE,
                effective_date=now,
                created_at=now,
                updated_at=now,
            )

            created = await repo.create(terms)
            await session.commit()

            print("\nTerms of Service created successfully!")
            print(f"   ID: {created.id}")
            print(f"   Type: {created.document_type.value}")
            print(f"   Version: {created.version}")
            print(f"   Status: {created.status.value}")
            print(f"   Effective: {created.effective_date}")
            print(f"   Length: {len(created.content)} characters")

    except Exception as e:
        print(f"\nError seeding Terms of Service: {e}")
        raise

    finally:
        await database.disconnect()
        print("\n" + "=" * 50)
        print("Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed_initial_terms())
