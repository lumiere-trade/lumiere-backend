"use client"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Bot, TrendingUp, Zap } from "lucide-react"
import { useState } from "react"

type FeatureType = "ai-designer" | "market-analysis" | "automated-execution" | null

export default function HomePage() {
  const [openFeature, setOpenFeature] = useState<FeatureType>(null)

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
    <div className="container mx-auto flex min-h-screen items-center justify-center px-6 pt-20">
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
          className="rounded-full px-20 py-8 text-2xl font-bold"
          onClick={() => window.location.href = 'http://localhost:3001'}
        >
          START TRADING
        </Button>
      </div>

      {openFeature && (
        <Dialog open={!!openFeature} onOpenChange={() => setOpenFeature(null)}>
          <DialogContent className="max-w-7xl max-h-[85vh] overflow-y-auto bg-background border-2 border-primary/30 rounded-2xl shadow-2xl">
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
                <div key={index} className="space-y-2 p-6 rounded-lg border border-primary/20 bg-card/50">
                  <h3 className="text-xl font-semibold text-primary">{section.header}</h3>
                  <p className="text-base leading-relaxed text-foreground">{section.content}</p>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
