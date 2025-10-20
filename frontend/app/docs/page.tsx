"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Search, ExternalLink } from "lucide-react"
import type { JSX } from "react/jsx-runtime"

const docsSections = [
  {
    title: "Getting Started",
    items: [
      { name: "Introduction", id: "introduction" },
      { name: "Quick Start", id: "quick-start" },
      { name: "Installation", id: "installation" },
    ],
  },
  {
    title: "Core Concepts",
    items: [
      { name: "Strategy Design", id: "strategy-design" },
      { name: "Prophet AI", id: "prophet-ai" },
      { name: "Backtesting", id: "backtesting" },
      { name: "Deployment", id: "deployment" },
    ],
  },
  {
    title: "Features",
    items: [
      { name: "Market Analysis", id: "market-analysis" },
      { name: "Technical Indicators", id: "technical-indicators" },
      { name: "Risk Management", id: "risk-management" },
      { name: "Performance Tracking", id: "performance-tracking" },
    ],
  },
  {
    title: "API Reference",
    items: [
      { name: "Authentication", id: "authentication", external: true },
      { name: "Strategy API", id: "strategy-api", external: true },
      { name: "Market Data API", id: "market-data-api", external: true },
    ],
  },
]

const docsContent: Record<string, { title: string; content: JSX.Element }> = {
  introduction: {
    title: "Introduction to Lumiere",
    content: (
      <div className="space-y-6">
        <p className="text-lg text-muted-foreground leading-relaxed">
          Welcome to Lumiere, the next generation of AI-driven trading platforms.
        </p>
        <h2 className="text-2xl font-bold text-foreground mt-8">What is Lumiere?</h2>
        <p className="text-muted-foreground leading-relaxed">
          Lumiere is an AI-powered trading strategy platform that transforms raw market data into winning strategies.
          Built for traders who value precision over emotion, Lumiere uses advanced artificial intelligence to turn
          market data into adaptive trading models that evolve with the markets.
        </p>
        <h2 className="text-2xl font-bold text-foreground mt-8">Key Features</h2>
        <ul className="list-disc list-inside space-y-2 text-muted-foreground">
          <li>Conversational AI strategy design with Prophet</li>
          <li>Advanced market analysis and backtesting</li>
          <li>Automated strategy deployment and execution</li>
          <li>Real-time performance monitoring and alerts</li>
        </ul>
      </div>
    ),
  },
  "quick-start": {
    title: "Quick Start Guide",
    content: (
      <div className="space-y-6">
        <p className="text-lg text-muted-foreground leading-relaxed">Get started with Lumiere in just a few minutes.</p>
        <h2 className="text-2xl font-bold text-foreground mt-8">Step 1: Connect Your Wallet</h2>
        <p className="text-muted-foreground leading-relaxed">
          Connect your Solana wallet (Phantom, Solflare, or other supported wallets) to begin using Lumiere.
        </p>
        <h2 className="text-2xl font-bold text-foreground mt-8">Step 2: Talk to Prophet AI</h2>
        <p className="text-muted-foreground leading-relaxed">
          Describe your trading goals and strategy ideas to Prophet AI. It will help you design a custom trading
          strategy tailored to your needs.
        </p>
        <h2 className="text-2xl font-bold text-foreground mt-8">Step 3: Backtest and Deploy</h2>
        <p className="text-muted-foreground leading-relaxed">
          Review your strategy's historical performance through backtesting, then deploy it for live trading when you're
          ready.
        </p>
      </div>
    ),
  },
  "prophet-ai": {
    title: "Prophet AI",
    content: (
      <div className="space-y-6">
        <p className="text-lg text-muted-foreground leading-relaxed">
          Meet Prophet, your personal AI strategy architect.
        </p>
        <h2 className="text-2xl font-bold text-foreground mt-8">What is Prophet AI?</h2>
        <p className="text-muted-foreground leading-relaxed">
          At the heart of Lumiere is Prophet, an advanced AI engine trained to understand trading logic, market
          structures, and human intent. It speaks your language — not just charts.
        </p>
        <h2 className="text-2xl font-bold text-foreground mt-8">How Prophet Works</h2>
        <p className="text-muted-foreground leading-relaxed">
          Prophet turns your ideas into structured trading models, backtests them against real data, and prepares them
          for live execution — all in one continuous, intelligent workflow.
        </p>
        <ul className="list-disc list-inside space-y-2 text-muted-foreground">
          <li>Natural language strategy design</li>
          <li>Intelligent parameter optimization</li>
          <li>Automated backtesting and validation</li>
          <li>Continuous learning and adaptation</li>
        </ul>
      </div>
    ),
  },
}

export default function DocsPage() {
  const [selectedDoc, setSelectedDoc] = useState("introduction")
  const [searchQuery, setSearchQuery] = useState("")

  const currentDoc = docsContent[selectedDoc] || docsContent.introduction

  return (
    <div className="flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border/50 bg-background/50 overflow-y-auto fixed left-0 top-20 bottom-0">
        <nav className="p-6 space-y-8">
          {docsSections.map((section) => (
            <div key={section.title}>
              <h3 className="text-xs font-semibold text-foreground uppercase tracking-wide mb-3">{section.title}</h3>
              <ul className="space-y-2">
                {section.items.map((item) => (
                  <li key={item.id}>
                    <button
                      onClick={() => setSelectedDoc(item.id)}
                      className={`flex items-center justify-between w-full text-sm py-2 px-3 rounded-lg transition-colors ${
                        selectedDoc === item.id
                          ? "bg-primary/10 text-primary font-medium"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                      }`}
                    >
                      <span>{item.name}</span>
                      {item.external && <ExternalLink className="w-3 h-3" />}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 mr-0 xl:mr-64 overflow-y-auto pb-20">
        <div className="container max-w-4xl mx-auto px-8 py-12">
          {/* Search Bar - moved inside content */}
          <div className="mb-8">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-background/50 border-border/50"
              />
              <kbd className="absolute right-3 top-1/2 -translate-y-1/2 px-2 py-1 text-xs text-muted-foreground bg-muted/50 rounded">
                Ctrl K
              </kbd>
            </div>
          </div>

          <h1 className="text-4xl font-bold text-foreground mb-4">{currentDoc.title}</h1>
          <div className="prose prose-invert max-w-none">{currentDoc.content}</div>
        </div>
      </main>

      {/* Right Sidebar - Table of Contents */}
      <aside className="w-64 border-l border-border/50 bg-background/50 overflow-y-auto fixed right-0 top-20 bottom-0 hidden xl:block">
        <nav className="p-6">
          <h3 className="text-xs font-semibold text-foreground uppercase tracking-wide mb-3">On This Page</h3>
          <ul className="space-y-2 text-sm">
            <li>
              <a href="#" className="text-primary hover:underline">
                What is Lumiere?
              </a>
            </li>
            <li>
              <a href="#" className="text-muted-foreground hover:text-foreground">
                Key Features
              </a>
            </li>
            <li>
              <a href="#" className="text-muted-foreground hover:text-foreground">
                Getting Started
              </a>
            </li>
          </ul>
        </nav>
      </aside>
    </div>
  )
}
