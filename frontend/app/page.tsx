"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import Link from "next/link"
import {
  Bot,
  TrendingUp,
  Zap,
  X,
  Settings,
  ChevronDown,
  Ghost,
  Sun,
  Backpack,
  Gem,
  Circle,
  Shield,
  Wallet,
} from "lucide-react"
import { Footer } from "@/components/footer"
import { useState } from "react"

type FeatureType = "ai-designer" | "market-analysis" | "automated-execution" | null

type WalletOption = {
  name: string
  icon: React.ComponentType<{ className?: string }>
  recent?: boolean
}

export default function HomePage() {
  const [openFeature, setOpenFeature] = useState<FeatureType>(null)
  const [showAuthDialog, setShowAuthDialog] = useState(false)
  const [showRpcSettings, setShowRpcSettings] = useState(false)
  const [selectedRpc, setSelectedRpc] = useState<"triton" | "syndica" | "custom">("triton")
  const [customRpc, setCustomRpc] = useState("")
  const [showAllWallets, setShowAllWallets] = useState(false)
  const [showTermsDialog, setShowTermsDialog] = useState(false)
  const [agreedToTerms, setAgreedToTerms] = useState(false)
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)

  const initialWallets: WalletOption[] = [
    { name: "Phantom", icon: Ghost, recent: true },
    { name: "Solflare", icon: Sun, recent: false },
    { name: "Backpack", icon: Backpack, recent: false },
    { name: "Binance Wallet", icon: Gem, recent: false },
  ]

  const additionalWallets: WalletOption[] = [
    { name: "OKX Wallet", icon: Zap, recent: false },
    { name: "Coinbase Wallet", icon: Circle, recent: false },
    { name: "Trust Wallet", icon: Shield, recent: false },
    { name: "MetaMask", icon: Wallet, recent: false },
  ]

  const displayedWallets = showAllWallets ? [...initialWallets, ...additionalWallets] : initialWallets

  const handleWalletClick = (walletName: string) => {
    setSelectedWallet(walletName)
    setShowAuthDialog(false)
    setShowTermsDialog(true)
  }

  const handleConfirmTerms = () => {
    if (agreedToTerms) {
      setShowTermsDialog(false)
      window.location.href = "/architect"
    }
  }

  const featureContent = {
    "ai-designer": {
      title: "AI Strategy Designer",
      icon: Bot,
      summary: "Your Personal Trading Strategy Architect",
      sections: [
        {
          header: "Natural Language Strategy Creation",
          content:
            "Prophet AI is powered by advanced language models trained specifically on trading logic and market structures. Simply describe your trading goals, risk tolerance, and preferred market conditions in plain English, and Prophet transforms your ideas into structured, executable trading strategies.",
        },
        {
          header: "Intelligent Strategy Design",
          content:
            "Prophet understands complex trading concepts like trend following, mean reversion, volatility breakouts, and custom indicator combinations. It doesn't just generate code—it designs intelligent trading logic tailored to your unique style, complete with entry/exit rules, position sizing, and risk management parameters.",
        },
        {
          header: "Iterative Refinement",
          content:
            "Work collaboratively with Prophet to refine your strategy. Ask questions, request modifications, and explore different approaches until you have a strategy that perfectly matches your vision and risk profile.",
        },
      ],
    },
    "market-analysis": {
      title: "Deep Market Analysis",
      icon: TrendingUp,
      summary: "Battle-Tested Strategies Through Historical Data",
      sections: [
        {
          header: "Comprehensive Data Analysis",
          content:
            "Lumiere analyzes years of historical market data using a comprehensive suite of technical indicators and mathematical models. Our AI engine processes price action, volume patterns, volatility metrics, momentum oscillators, and custom indicators to identify unique market patterns invisible to the human eye.",
        },
        {
          header: "Advanced Backtesting",
          content:
            "The system backtests strategies against real historical data, simulating thousands of trades to evaluate performance across different market conditions including bull markets, bear markets, and high volatility periods. This ensures your strategy is robust and adaptable.",
        },
        {
          header: "Detailed Performance Metrics",
          content:
            "Get comprehensive analytics on win rates, maximum drawdowns, Sharpe ratios, profit factors, and risk-adjusted returns. Understand exactly how your strategy performs before risking real capital, with transparent reporting on every aspect of strategy performance.",
        },
      ],
    },
    "automated-execution": {
      title: "Automated Execution",
      icon: Zap,
      summary: "Institutional-Grade Trading Infrastructure",
      sections: [
        {
          header: "24/7 Market Monitoring",
          content:
            "Once your strategy is ready, Lumiere deploys it to live markets with institutional-grade execution infrastructure. Your strategies monitor markets around the clock in real-time, reacting instantly to price movements and market conditions without human intervention or emotional bias.",
        },
        {
          header: "Built-In Risk Management",
          content:
            "Automated risk management tracks position sizes, stop losses, take profits, and portfolio exposure in real-time. The system enforces your predefined risk parameters automatically, protecting your capital even when you're not actively monitoring the markets.",
        },
        {
          header: "Real-Time Performance Tracking",
          content:
            "Monitor your strategies with live P&L updates, instant trade notifications, and detailed execution logs. You maintain full control with the ability to pause, modify, or stop strategies at any time, while Lumiere handles the complex execution logic behind the scenes.",
        },
      ],
    },
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto flex items-center justify-between px-6 py-4">
          <Link href="/" className="flex flex-col hover:opacity-80 transition-opacity">
            <div className="text-2xl font-bold tracking-wider text-primary">LUMIERE</div>
            <p className="text-[13px] text-muted-foreground tracking-wide">Blind to emotion, guided by algorithm</p>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/docs">
              <Button variant="outline" size="lg" className="rounded-full px-6 font-semibold bg-transparent">
                DOCS
              </Button>
            </Link>
            <Link href="/learn-more">
              <Button variant="outline" size="lg" className="rounded-full px-6 font-semibold bg-transparent">
                LEARN MORE
              </Button>
            </Link>
            <Button
              variant="outline"
              size="lg"
              className="rounded-full px-8 font-semibold bg-transparent"
              onClick={() => setShowAuthDialog(true)}
            >
              CONNECT WALLET
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto flex min-h-screen items-center justify-center px-6 pt-20">
        <div className="flex flex-col items-center text-center max-w-7xl w-full">
          <div className="mb-12 flex flex-col items-center w-full">
            <div className="w-full max-w-2xl h-1 bg-foreground/20 mb-6" />
            <h1 className="text-8xl font-bold tracking-wider text-primary mb-6">LUMIERE</h1>
            <div className="w-full max-w-2xl h-1 bg-foreground/20" />
          </div>

          <div className="mb-16 space-y-4">
            <p className="text-3xl font-semibold text-foreground">AI-Powered Trading Strategy Platform</p>
            <p className="max-w-3xl text-lg leading-relaxed text-muted-foreground">
              Transform raw market data into winning strategies with the power of AI. Lumiere combines advanced market
              analysis, intelligent backtesting, and automated deployment to help you trade smarter, not harder.
            </p>
          </div>

          <div className="mb-16 grid grid-cols-1 md:grid-cols-3 gap-12 w-full">
            <div
              onClick={() => setOpenFeature("ai-designer")}
              className="flex flex-col items-center gap-4 cursor-pointer transition-colors"
            >
              <div className="rounded-full bg-primary/10 p-6 transition-colors hover:bg-primary/20">
                <Bot className="w-12 h-12 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-primary">AI Strategy Designer</h3>
              <p className="text-base text-muted-foreground leading-relaxed">
                Chat with Prophet AI to create custom trading strategies tailored to your goals
              </p>
            </div>
            <div
              onClick={() => setOpenFeature("market-analysis")}
              className="flex flex-col items-center gap-4 cursor-pointer transition-colors"
            >
              <div className="rounded-full bg-primary/10 p-6 transition-colors hover:bg-primary/20">
                <TrendingUp className="w-12 h-12 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-primary">Deep Market Analysis</h3>
              <p className="text-base text-muted-foreground leading-relaxed">
                Analyze years of historical data with advanced technical indicators
              </p>
            </div>
            <div
              onClick={() => setOpenFeature("automated-execution")}
              className="flex flex-col items-center gap-4 cursor-pointer transition-colors"
            >
              <div className="rounded-full bg-primary/10 p-6 transition-colors hover:bg-primary/20">
                <Zap className="w-12 h-12 text-primary" />
              </div>
              <h3 className="text-xl font-bold text-primary">Automated Execution</h3>
              <p className="text-base text-muted-foreground leading-relaxed">
                Deploy strategies instantly with real-time monitoring and alerts
              </p>
            </div>
          </div>

          <Button
            size="lg"
            className="rounded-full px-20 py-8 text-2xl font-bold transition-all duration-300 hover:brightness-110 hover:ring-2 hover:ring-primary/30"
            onClick={() => setShowAuthDialog(true)}
          >
            START TRADING
          </Button>
        </div>
      </main>

      {openFeature && (
        <Dialog open={!!openFeature} onOpenChange={() => setOpenFeature(null)}>
          <DialogContent className="max-w-5xl max-h-[80vh] overflow-y-auto bg-background border-2 border-primary/30 rounded-2xl shadow-2xl">
            <DialogHeader>
              <div className="flex items-center gap-4 mb-6">
                <div className="rounded-full bg-primary/10 p-4">
                  {openFeature === "ai-designer" && <Bot className="w-10 h-10 text-primary" />}
                  {openFeature === "market-analysis" && <TrendingUp className="w-10 h-10 text-primary" />}
                  {openFeature === "automated-execution" && <Zap className="w-10 h-10 text-primary" />}
                </div>
                <div>
                  <DialogTitle className="text-3xl font-bold text-primary mb-2">
                    {featureContent[openFeature].title}
                  </DialogTitle>
                  <p className="text-lg text-muted-foreground">{featureContent[openFeature].summary}</p>
                </div>
              </div>
            </DialogHeader>
            <div className="space-y-6 mt-4">
              {featureContent[openFeature].sections.map((section, index) => (
                <div key={index} className="space-y-2">
                  <h3 className="text-xl font-semibold text-primary">{section.header}</h3>
                  <p className="text-base leading-relaxed text-foreground">{section.content}</p>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {showAuthDialog && !showRpcSettings && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setShowAuthDialog(false)}
        >
          <div
            className="relative w-full max-w-lg max-h-[90vh] mx-4 bg-background rounded-2xl border-2 border-primary/30 shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowAuthDialog(false)}
              className="absolute top-6 right-6 text-muted-foreground hover:text-primary transition-colors z-10"
            >
              <X className="h-5 w-5" />
            </button>

            <button
              onClick={() => setShowRpcSettings(true)}
              className="absolute top-6 right-16 text-muted-foreground hover:text-primary transition-colors z-10"
            >
              <Settings className="h-5 w-5" />
            </button>

            <div className="p-8 space-y-6 flex-1 overflow-hidden flex flex-col">
              <div className="text-center space-y-2 flex-shrink-0">
                <h1 className="text-3xl font-bold tracking-tight text-primary">Connect Wallet</h1>
                <p className="text-sm text-muted-foreground">
                  Secure and simple. Lumiere is independently audited, with you in full control of your funds.
                </p>
              </div>

              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full pr-4">
                  <div className="space-y-3">
                    {displayedWallets.map((wallet) => {
                      const IconComponent = wallet.icon
                      return (
                        <button
                          key={wallet.name}
                          onClick={() => handleWalletClick(wallet.name)}
                          className="w-full flex items-center justify-between p-4 rounded-xl bg-card/20 hover:bg-card/30 border border-border/30 hover:border-primary/20 transition-all group"
                        >
                          <div className="flex items-center gap-4">
                            <div className="rounded-lg bg-primary/10 p-2">
                              <IconComponent className="w-6 h-6 text-primary" />
                            </div>
                            <span className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                              {wallet.name}
                            </span>
                          </div>
                          {wallet.recent && (
                            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-primary/20 text-primary border border-primary/30">
                              Recent
                            </span>
                          )}
                        </button>
                      )
                    })}
                  </div>
                </ScrollArea>
              </div>

              {!showAllWallets && (
                <button
                  onClick={() => setShowAllWallets(true)}
                  className="w-full flex items-center justify-center gap-2 py-3 text-primary hover:text-primary/80 transition-colors font-semibold flex-shrink-0"
                >
                  <ChevronDown className="h-5 w-5" />
                  <span>All Wallets</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {showRpcSettings && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setShowRpcSettings(false)}
        >
          <div
            className="relative w-full max-w-lg mx-4 bg-background rounded-2xl border-2 border-primary/30 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowRpcSettings(false)}
              className="absolute top-6 left-6 text-muted-foreground hover:text-primary transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="p-8 space-y-6">
              <div className="text-center">
                <h1 className="text-3xl font-bold tracking-tight text-primary">Settings</h1>
              </div>

              <div className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground">RPC Endpoint</h2>

                <button
                  onClick={() => setSelectedRpc("triton")}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${
                    selectedRpc === "triton"
                      ? "bg-primary/10 border-primary"
                      : "bg-card/20 border-border/30 hover:border-primary/20"
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedRpc === "triton" ? "border-primary" : "border-muted-foreground/30"
                    }`}
                  >
                    {selectedRpc === "triton" && <div className="w-3 h-3 rounded-full bg-primary" />}
                  </div>
                  <span className="text-base font-medium text-foreground">Mainnet Beta (Triton)</span>
                </button>

                <button
                  onClick={() => setSelectedRpc("syndica")}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${
                    selectedRpc === "syndica"
                      ? "bg-primary/10 border-primary"
                      : "bg-card/20 border-border/30 hover:border-primary/20"
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedRpc === "syndica" ? "border-primary" : "border-muted-foreground/30"
                    }`}
                  >
                    {selectedRpc === "syndica" && <div className="w-3 h-3 rounded-full bg-primary" />}
                  </div>
                  <span className="text-base font-medium text-foreground">Syndica</span>
                </button>

                <button
                  onClick={() => setSelectedRpc("custom")}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${
                    selectedRpc === "custom"
                      ? "bg-primary/10 border-primary"
                      : "bg-card/20 border-border/30 hover:border-primary/20"
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedRpc === "custom" ? "border-primary" : "border-muted-foreground/30"
                    }`}
                  >
                    {selectedRpc === "custom" && <div className="w-3 h-3 rounded-full bg-primary" />}
                  </div>
                  <span className="text-base font-medium text-foreground">Custom</span>
                </button>

                {selectedRpc === "custom" && (
                  <input
                    type="text"
                    placeholder="Enter custom RPC"
                    value={customRpc}
                    onChange={(e) => setCustomRpc(e.target.value)}
                    className="w-full p-4 rounded-xl bg-card/20 border border-border/30 focus:border-primary focus:outline-none text-foreground placeholder:text-muted-foreground"
                  />
                )}
              </div>

              <Button
                onClick={() => setShowRpcSettings(false)}
                className="w-full rounded-full py-6 text-lg font-bold bg-primary hover:bg-primary/90 text-black"
              >
                Save Settings
              </Button>
            </div>
          </div>
        </div>
      )}

      <Dialog open={showTermsDialog} onOpenChange={setShowTermsDialog}>
        <DialogContent className="max-w-2xl bg-background border-2 border-primary/30 rounded-2xl shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-primary">Terms of Use & Legal Agreements</DialogTitle>
          </DialogHeader>

          <ScrollArea className="h-[400px] rounded-md border border-border/30 p-6">
            <div className="space-y-6 text-sm">
              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">1. Acceptance of Terms</h3>
                <p className="text-muted-foreground">
                  By accessing and using LUMIERE, you accept and agree to be bound by the terms and provision of this
                  agreement. If you do not agree to these terms, please do not use our service.
                </p>
              </section>

              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">2. Trading Risks</h3>
                <p className="text-muted-foreground">
                  Trading cryptocurrencies and digital assets involves substantial risk of loss. You acknowledge that:
                </p>
                <ul className="ml-6 mt-2 list-disc space-y-1 text-muted-foreground">
                  <li>Past performance does not guarantee future results</li>
                  <li>You may lose some or all of your invested capital</li>
                  <li>Market conditions can change rapidly and unpredictably</li>
                  <li>Automated trading strategies carry inherent risks</li>
                </ul>
              </section>

              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">3. Service Description</h3>
                <p className="text-muted-foreground">
                  LUMIERE provides AI-assisted trading strategy creation and deployment tools. We do not provide
                  financial advice, and our services should not be construed as such. All trading decisions are made at
                  your own discretion and risk.
                </p>
              </section>

              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">4. User Responsibilities</h3>
                <p className="text-muted-foreground">You agree to:</p>
                <ul className="ml-6 mt-2 list-disc space-y-1 text-muted-foreground">
                  <li>Maintain the security of your wallet and account credentials</li>
                  <li>Comply with all applicable laws and regulations</li>
                  <li>Not use the service for illegal activities</li>
                  <li>Monitor your trading activities and strategies regularly</li>
                </ul>
              </section>

              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">5. Limitation of Liability</h3>
                <p className="text-muted-foreground">
                  LUMIERE and its operators shall not be liable for any direct, indirect, incidental, special, or
                  consequential damages resulting from the use or inability to use our service, including but not
                  limited to trading losses, data loss, or service interruptions.
                </p>
              </section>

              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">6. Privacy & Data</h3>
                <p className="text-muted-foreground">
                  We collect and process data necessary to provide our services. Your wallet address and trading data
                  may be stored and analyzed to improve strategy performance. We do not sell your personal information
                  to third parties.
                </p>
              </section>

              <section>
                <h3 className="mb-2 text-lg font-semibold text-primary">7. Modifications</h3>
                <p className="text-muted-foreground">
                  We reserve the right to modify these terms at any time. Continued use of the service after changes
                  constitutes acceptance of the modified terms.
                </p>
              </section>
            </div>
          </ScrollArea>

          <div className="flex items-center space-x-2 rounded-md border border-border/30 p-4">
            <Checkbox
              id="terms"
              checked={agreedToTerms}
              onCheckedChange={(checked) => setAgreedToTerms(checked as boolean)}
            />
            <label
              htmlFor="terms"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              I have read and agree to the Terms of Use and Legal Agreements
            </label>
          </div>

          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={() => setShowTermsDialog(false)} className="rounded-full">
              Cancel
            </Button>
            <Button onClick={handleConfirmTerms} disabled={!agreedToTerms} className="rounded-full">
              Confirm & Continue
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Footer />
    </div>
  )
}
