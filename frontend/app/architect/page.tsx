"use client"

import type React from "react"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { NavigationHeader } from "@/components/navigation-header"
import {
  Sparkles,
  Send,
  TrendingUp,
  TrendingDown,
  Activity,
  ChevronDown,
  ChevronUp,
  Check,
  Lightbulb,
  Plus,
  X,
  Pencil,
  Minimize2,
  MessageCircle,
} from "lucide-react"

const initialStrategies = [
  {
    id: 1,
    name: "RSI Momentum",
    asset: "SOL/USD",
    winRate: "67.3%",
    createdAt: "2024-01-15",
  },
  {
    id: 2,
    name: "MA Crossover",
    asset: "BTC/USD",
    winRate: "72.1%",
    createdAt: "2024-01-10",
  },
  {
    id: 3,
    name: "Breakout Strategy",
    asset: "ETH/USD",
    winRate: "64.8%",
    createdAt: "2024-01-08",
  },
]

export default function ArchitectPage() {
  const [savedStrategies, setSavedStrategies] = useState(initialStrategies)
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to the Architect! I am Prophet, your AI strategy advisor. I will help you forge winning strategies from raw market data. What asset would you like to trade?",
    },
  ])
  const [input, setInput] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedAsset, setSelectedAsset] = useState("SOL/USD")
  const [openSection, setOpenSection] = useState<"strategies" | "chat">("chat")
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null)
  const [hasStartedAnalysis, setHasStartedAnalysis] = useState(false)
  const [viewMode, setViewMode] = useState<"view" | "edit">("view")
  const [editingStrategyId, setEditingStrategyId] = useState<number | null>(null)
  const [strategyParams, setStrategyParams] = useState({
    rsiPeriod: 14,
    rsiOverbought: 70,
    rsiOversold: 30,
    maShortPeriod: 10,
    maLongPeriod: 50,
    stopLoss: 2.5,
    takeProfit: 5.0,
    timeframe: "15m",
  })

  const examplePrompts = [
    "Create a momentum strategy for SOL/USD",
    "Analyze BTC/USD with RSI indicators",
    "Build a breakout strategy for ETH/USD",
  ]

  const handleNewStrategy = () => {
    setSelectedStrategy(null)
    setHasStartedAnalysis(false)
    setMessages([
      {
        role: "assistant",
        content:
          "Welcome to the Architect! I am Prophet, your AI strategy advisor. I will help you forge winning strategies from raw market data. What asset would you like to trade?",
      },
    ])
    setOpenSection("chat")
  }

  const handleDeleteStrategy = (strategyId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setSavedStrategies(savedStrategies.filter((s) => s.id !== strategyId))
    if (selectedStrategy === strategyId) {
      setSelectedStrategy(null)
      setHasStartedAnalysis(false)
    }
  }

  const handleSend = () => {
    if (!input.trim()) return

    setMessages([...messages, { role: "user", content: input }])
    setInput("")
    setIsAnalyzing(true)
    setHasStartedAnalysis(true)

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Excellent! I'm analyzing SOL/USD market data from Chronicler. I've identified strong momentum patterns and optimal entry points. Would you like me to create a strategy based on RSI and moving average crossovers?",
        },
      ])
      setIsAnalyzing(false)
    }, 2000)
  }

  const handleSelectStrategy = (strategyId: number) => {
    setSelectedStrategy(strategyId)
    setHasStartedAnalysis(true)
    const strategy = savedStrategies.find((s) => s.id === strategyId)
    if (strategy) {
      setSelectedAsset(strategy.asset)
      setMessages([
        ...messages,
        {
          role: "assistant",
          content: `Loaded strategy "${strategy.name}" for ${strategy.asset}. This strategy has a win rate of ${strategy.winRate}. Would you like to modify it or run a new backtest?`,
        },
      ])
    }
  }

  const handleExamplePrompt = (prompt: string) => {
    setInput(prompt)
    setMessages([...messages, { role: "user", content: prompt }])
    setIsAnalyzing(true)
    setHasStartedAnalysis(true)

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Excellent! I'm analyzing the market data from Chronicler. I've identified strong patterns and optimal entry points. Would you like me to create a detailed strategy based on these insights?",
        },
      ])
      setIsAnalyzing(false)
    }, 2000)
  }

  const handleEditStrategy = (strategyId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingStrategyId(strategyId)
    setSelectedStrategy(strategyId)
    setHasStartedAnalysis(true)
    setViewMode("edit")
    const strategy = savedStrategies.find((s) => s.id === strategyId)
    if (strategy) {
      setSelectedAsset(strategy.asset)
    }
  }

  const handleSaveStrategy = () => {
    setViewMode("view")
    setMessages([
      ...messages,
      {
        role: "assistant",
        content: `Strategy parameters updated successfully! The changes have been saved and you can now run a new backtest with the updated parameters.`,
      },
    ])
  }

  const handleDiscardChanges = () => {
    setViewMode("view")
    // Reset to original parameters if needed
  }

  const [chatMode, setChatMode] = useState<"popup" | "sidebar">("popup")
  const [showWelcomePopup, setShowWelcomePopup] = useState(true)

  useEffect(() => {
    if (showWelcomePopup) {
      setChatMode("popup")
    }
  }, [showWelcomePopup])

  const handleMinimizeChat = () => {
    setChatMode("sidebar")
    setShowWelcomePopup(false)
  }

  const handleExpandChat = () => {
    setChatMode("popup")
  }

  const handleClosePopup = () => {
    setShowWelcomePopup(false)
    setChatMode("sidebar")
  }

  const handleSendInPopup = () => {
    if (!input.trim()) return

    setMessages([...messages, { role: "user", content: input }])
    setInput("")
    setIsAnalyzing(true)
    setHasStartedAnalysis(true)
    setShowWelcomePopup(false)
    setChatMode("sidebar")

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Excellent! I'm analyzing SOL/USD market data from Chronicler. I've identified strong momentum patterns and optimal entry points. Would you like me to create a strategy based on RSI and moving average crossovers?",
        },
      ])
      setIsAnalyzing(false)
    }, 2000)
  }

  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader currentPage="forger" />

      <Dialog open={chatMode === "popup"} onOpenChange={(open) => !open && handleClosePopup()}>
        <DialogContent className="max-w-3xl max-h-[85vh] bg-[#2a1f1a] border-2 border-primary/30 rounded-2xl shadow-2xl backdrop-blur-xl">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-3">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-primary">Welcome to Prophet AI</h2>
                <p className="text-sm text-muted-foreground">Your AI Strategy Advisor</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleMinimizeChat}
              className="h-8 w-8 rounded-full hover:bg-primary/10"
              title="Minimize to sidebar"
            >
              <Minimize2 className="h-4 w-4" />
            </Button>
          </div>

          <div className="my-6 space-y-4 max-h-[50vh] overflow-y-auto">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`w-full ${
                    message.role === "user"
                      ? "bg-primary/5 border-l-2 border-primary pl-4 pr-2"
                      : "bg-transparent pl-2 pr-4"
                  } py-3`}
                >
                  {message.role === "assistant" && (
                    <div className="mb-2 flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-primary" />
                      <span className="text-sm font-semibold text-primary">Prophet</span>
                    </div>
                  )}
                  {message.role === "user" && (
                    <div className="mb-2 flex items-center justify-end gap-2">
                      <span className="text-sm font-semibold text-foreground">You</span>
                    </div>
                  )}
                  <p className="text-sm leading-relaxed">{message.content}</p>
                </div>
              </div>
            ))}
            {isAnalyzing && (
              <div className="flex justify-start">
                <div className="w-full bg-transparent py-3 pl-2 pr-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="text-sm font-semibold text-primary">Prophet</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:0.2s]" />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:0.4s]" />
                  </div>
                </div>
              </div>
            )}

            {!hasStartedAnalysis && (
              <div className="space-y-3 mt-4">
                <p className="text-sm font-semibold text-muted-foreground">QUICK START PROMPTS</p>
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setInput(prompt)
                      handleSendInPopup()
                    }}
                    className="w-full rounded-lg border border-primary/30 bg-card/50 px-4 py-3 text-left text-sm transition-all hover:border-primary hover:bg-card"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <textarea
              placeholder="Ask Prophet anything... (Press Enter to send, Shift+Enter for new line)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSendInPopup()
                }
              }}
              className="w-full min-h-[100px] rounded-lg border border-primary/30 bg-background px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground/60">Minimize to sidebar for compact view while working</p>
              <Button size="sm" className="rounded-full" onClick={handleSendInPopup}>
                <Send className="h-4 w-4 mr-2" />
                Send
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <div className="flex h-[calc(100vh-80px)] pt-20">
        <div className="flex w-80 flex-col border-r border-border">
          <div className="border-b border-border">
            <button
              onClick={() => setOpenSection(openSection === "strategies" ? "chat" : "strategies")}
              className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-card/30"
            >
              <div>
                <h3 className="text-sm font-bold text-primary">SAVED STRATEGIES</h3>
                <p className="text-xs text-muted-foreground">{savedStrategies.length} strategies</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleNewStrategy()
                  }}
                  className="rounded-full bg-primary/10 p-1 transition-colors hover:bg-primary/20"
                  title="Create new strategy"
                >
                  <Plus className="h-4 w-4 text-primary" />
                </button>
                {openSection === "strategies" ? (
                  <ChevronUp className="h-4 w-4 text-primary" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-primary" />
                )}
              </div>
            </button>

            {openSection === "strategies" && (
              <div className="max-h-[calc(100vh-200px)] space-y-2 overflow-y-auto p-3">
                {savedStrategies.map((strategy) => (
                  <button
                    key={strategy.id}
                    onClick={() => handleSelectStrategy(strategy.id)}
                    className={`group relative w-full rounded-lg border p-3 text-left transition-all hover:border-primary/50 hover:bg-card/50 ${
                      selectedStrategy === strategy.id ? "border-primary bg-card" : "border-border bg-card/20"
                    }`}
                  >
                    <div className="absolute right-2 top-2 flex gap-1">
                      <button
                        onClick={(e) => handleEditStrategy(strategy.id, e)}
                        className="rounded-full bg-background/80 p-1 opacity-0 transition-opacity hover:bg-primary/20 group-hover:opacity-100"
                        title="Edit strategy"
                      >
                        <Pencil className="h-3 w-3 text-primary" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteStrategy(strategy.id, e)}
                        className="rounded-full bg-background/80 p-1 opacity-0 transition-opacity hover:bg-destructive/20 group-hover:opacity-100"
                        title="Delete strategy"
                      >
                        <X className="h-3 w-3 text-destructive" />
                      </button>
                    </div>
                    {selectedStrategy === strategy.id && (
                      <div className="absolute right-2 top-2 opacity-100 group-hover:opacity-0">
                        <Check className="h-3 w-3 text-primary" />
                      </div>
                    )}
                    <div className="mb-1 pr-12">
                      <h4 className="text-xs font-semibold text-foreground">{strategy.name}</h4>
                      <p className="text-xs text-muted-foreground">{strategy.asset}</p>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-green-500">{strategy.winRate}</span>
                      <span className="text-muted-foreground/60">{strategy.createdAt}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-1 flex-col border-b border-border">
            <button
              onClick={() => setOpenSection(openSection === "chat" ? "strategies" : "chat")}
              className="flex w-full items-center justify-between border-b border-border p-4 text-left transition-colors hover:bg-card/30"
            >
              <div>
                <div className="mb-1 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-bold text-primary">PROPHET AI</h3>
                </div>
                <p className="text-xs text-muted-foreground">Strategy Advisor</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleExpandChat()
                  }}
                  className="rounded-full bg-primary/10 p-1 transition-colors hover:bg-primary/20"
                  title="Expand chat to popup"
                >
                  <MessageCircle className="h-4 w-4 text-primary" />
                </button>
                {openSection === "chat" ? (
                  <ChevronUp className="h-4 w-4 text-primary" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-primary" />
                )}
              </div>
            </button>

            {openSection === "chat" && (
              <div className="flex flex-1 flex-col p-4">
                <div className="mb-3 flex-1 space-y-2 overflow-y-auto rounded-lg border border-border bg-card/30 p-3">
                  {messages.map((message, index) => (
                    <div key={index} className="w-full">
                      <div
                        className={`${
                          message.role === "user"
                            ? "bg-primary/5 border-l-2 border-primary pl-3 pr-2"
                            : "bg-transparent pl-2 pr-3"
                        } py-2`}
                      >
                        {message.role === "assistant" && (
                          <div className="mb-1 flex items-center gap-1 text-xs text-primary">
                            <Sparkles className="h-3 w-3" />
                            <span className="font-semibold">Prophet</span>
                          </div>
                        )}
                        {message.role === "user" && (
                          <div className="mb-1 flex items-center justify-end gap-1 text-xs text-foreground">
                            <span className="font-semibold">You</span>
                          </div>
                        )}
                        <p className="text-xs leading-relaxed">{message.content}</p>
                      </div>
                    </div>
                  ))}
                  {isAnalyzing && (
                    <div className="w-full">
                      <div className="bg-transparent py-2 pl-2 pr-3">
                        <div className="mb-1 flex items-center gap-1 text-xs text-primary">
                          <Sparkles className="h-3 w-3" />
                          <span className="font-semibold">Prophet</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                          <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:0.2s]" />
                          <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:0.4s]" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <p className="mb-2 text-center text-xs text-muted-foreground/60">
                  Click <MessageCircle className="inline h-3 w-3" /> above for expanded view
                </p>

                <div className="flex gap-2">
                  <Input
                    placeholder="Ask Prophet..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    className="rounded-full border-primary/30 bg-card text-xs"
                  />
                  <Button size="icon" className="h-9 w-9 shrink-0 rounded-full" onClick={handleSend}>
                    <Send className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side - Takes up more space for charts and metrics */}
        <div className="flex-1 overflow-y-auto p-6">
          {!hasStartedAnalysis ? (
            <div className="flex h-full items-center justify-center">
              <div className="max-w-2xl text-center">
                <div className="mb-6 flex justify-center">
                  <div className="rounded-full bg-primary/10 p-6">
                    <Sparkles className="h-16 w-16 text-primary" />
                  </div>
                </div>

                <h2 className="mb-3 text-3xl font-bold text-primary">Welcome to the Architect</h2>
                <p className="mb-8 text-lg text-muted-foreground leading-relaxed">
                  Start a conversation with Prophet AI to forge winning trading strategies from raw market data.
                </p>

                <div className="mb-8 space-y-4">
                  <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-card/50 p-4 text-left">
                    <Lightbulb className="mt-1 h-5 w-5 shrink-0 text-primary" />
                    <div>
                      <h3 className="mb-1 font-semibold text-foreground">How it works</h3>
                      <p className="text-sm text-muted-foreground">
                        Chat with Prophet about your trading goals. Prophet will analyze market data, suggest
                        strategies, and help you backtest them.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mb-4">
                  <p className="mb-3 text-sm font-semibold text-muted-foreground">TRY THESE PROMPTS</p>
                  <div className="space-y-2">
                    {examplePrompts.map((prompt, index) => (
                      <button
                        key={index}
                        onClick={() => handleExamplePrompt(prompt)}
                        className="w-full rounded-full border border-primary/30 bg-card/30 px-6 py-3 text-sm transition-all hover:border-primary hover:bg-card"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-muted-foreground/60">
                  Or start typing in the chat to begin your strategy creation journey
                </p>
              </div>
            </div>
          ) : viewMode === "edit" ? (
            <>
              <div className="mb-6">
                <h2 className="mb-2 text-2xl font-bold text-primary">EDIT STRATEGY</h2>
                <p className="text-sm text-muted-foreground">
                  Modify parameters for {savedStrategies.find((s) => s.id === editingStrategyId)?.name}
                </p>
              </div>

              <Card className="mb-6 border-primary/20 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold text-primary">RSI Indicator Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="mb-2 block text-sm text-muted-foreground">RSI Period</label>
                    <Input
                      type="number"
                      value={strategyParams.rsiPeriod}
                      onChange={(e) => setStrategyParams({ ...strategyParams, rsiPeriod: Number(e.target.value) })}
                      className="border-primary/30 bg-background"
                    />
                    <p className="mt-1 text-xs text-muted-foreground/60">Number of periods for RSI calculation</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">Overbought Level</label>
                      <Input
                        type="number"
                        value={strategyParams.rsiOverbought}
                        onChange={(e) =>
                          setStrategyParams({ ...strategyParams, rsiOverbought: Number(e.target.value) })
                        }
                        className="border-primary/30 bg-background"
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">Oversold Level</label>
                      <Input
                        type="number"
                        value={strategyParams.rsiOversold}
                        onChange={(e) => setStrategyParams({ ...strategyParams, rsiOversold: Number(e.target.value) })}
                        className="border-primary/30 bg-background"
                      />
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="mb-6 border-primary/20 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold text-primary">Moving Average Settings</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-2 block text-sm text-muted-foreground">Short MA Period</label>
                    <Input
                      type="number"
                      value={strategyParams.maShortPeriod}
                      onChange={(e) => setStrategyParams({ ...strategyParams, maShortPeriod: Number(e.target.value) })}
                      className="border-primary/30 bg-background"
                    />
                    <p className="mt-1 text-xs text-muted-foreground/60">Fast moving average</p>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm text-muted-foreground">Long MA Period</label>
                    <Input
                      type="number"
                      value={strategyParams.maLongPeriod}
                      onChange={(e) => setStrategyParams({ ...strategyParams, maLongPeriod: Number(e.target.value) })}
                      className="border-primary/30 bg-background"
                    />
                    <p className="mt-1 text-xs text-muted-foreground/60">Slow moving average</p>
                  </div>
                </div>
              </Card>

              <Card className="mb-6 border-primary/20 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold text-primary">Risk Management</h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">Stop Loss (%)</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={strategyParams.stopLoss}
                        onChange={(e) => setStrategyParams({ ...strategyParams, stopLoss: Number(e.target.value) })}
                        className="border-primary/30 bg-background"
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm text-muted-foreground">Take Profit (%)</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={strategyParams.takeProfit}
                        onChange={(e) => setStrategyParams({ ...strategyParams, takeProfit: Number(e.target.value) })}
                        className="border-primary/30 bg-background"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-muted-foreground">Timeframe</label>
                    <select
                      value={strategyParams.timeframe}
                      onChange={(e) => setStrategyParams({ ...strategyParams, timeframe: e.target.value })}
                      className="w-full rounded-md border border-primary/30 bg-background px-3 py-2 text-sm"
                    >
                      <option value="5m">5 minutes</option>
                      <option value="15m">15 minutes</option>
                      <option value="1h">1 hour</option>
                      <option value="4h">4 hours</option>
                      <option value="1d">1 day</option>
                    </select>
                  </div>
                </div>
              </Card>

              <div className="flex gap-3">
                <Button onClick={handleSaveStrategy} className="flex-1 rounded-full py-6 text-lg font-bold">
                  SAVE CHANGES
                </Button>
                <Button
                  onClick={handleDiscardChanges}
                  variant="outline"
                  className="flex-1 rounded-full border-primary/30 bg-transparent py-6 text-lg font-bold"
                >
                  DISCARD
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="mb-2 text-2xl font-bold text-primary">STRATEGY METRICS</h2>
                <p className="text-sm text-muted-foreground">Real-time analysis and performance indicators</p>
              </div>

              <Card className="mb-6 border-primary/20 bg-card p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-lg font-bold text-primary">{selectedAsset}</h3>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 rounded-full border-primary/30 bg-primary/10 px-3 text-xs"
                    >
                      Candles
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 rounded-full px-3 text-xs">
                      Line
                    </Button>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 rounded-full border-primary/30 bg-primary/10 px-3 text-xs"
                  >
                    15m
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 rounded-full px-3 text-xs">
                    1h
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 rounded-full px-3 text-xs">
                    4h
                  </Button>
                </div>
              </Card>

              <Card className="mb-6 border-primary/20 bg-card p-4">
                <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-background/50">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Activity className="mx-auto mb-2 h-12 w-12 text-primary/30" />
                      <p className="text-sm text-muted-foreground">Chart visualization</p>
                      <p className="text-xs text-muted-foreground/60">Market data will appear here</p>
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-[linear-gradient(rgba(212,175,122,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(212,175,122,0.05)_1px,transparent_1px)] bg-[size:40px_40px]" />
                </div>
              </Card>

              <div className="mb-6 grid grid-cols-2 gap-4">
                <Card className="border-primary/20 bg-card p-4">
                  <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <TrendingUp className="h-3 w-3" />
                    <span>Win Rate</span>
                  </div>
                  <p className="text-2xl font-bold text-primary">67.3%</p>
                  <p className="text-xs text-green-500">+2.4% vs baseline</p>
                </Card>

                <Card className="border-primary/20 bg-card p-4">
                  <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <Activity className="h-3 w-3" />
                    <span>Sharpe Ratio</span>
                  </div>
                  <p className="text-2xl font-bold text-primary">1.84</p>
                  <p className="text-xs text-green-500">Excellent risk/reward</p>
                </Card>

                <Card className="border-primary/20 bg-card p-4">
                  <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <TrendingUp className="h-3 w-3" />
                    <span>Max Drawdown</span>
                  </div>
                  <p className="text-2xl font-bold text-primary">-12.4%</p>
                  <p className="text-xs text-yellow-500">Moderate risk</p>
                </Card>

                <Card className="border-primary/20 bg-card p-4">
                  <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <TrendingDown className="h-3 w-3" />
                    <span>Avg Trade</span>
                  </div>
                  <p className="text-2xl font-bold text-primary">+3.2%</p>
                  <p className="text-xs text-green-500">Strong performance</p>
                </Card>
              </div>

              <Card className="mb-6 border-primary/20 bg-card p-4">
                <h3 className="mb-3 font-semibold text-primary">Strategy Parameters</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Indicator</span>
                    <span className="font-medium">RSI + MA Crossover</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Timeframe</span>
                    <span className="font-medium">15m</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Backtest Period</span>
                    <span className="font-medium">2 years</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Data Points</span>
                    <span className="font-medium">48,320</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <span className="font-medium text-green-500">Analyzing</span>
                  </div>
                </div>
              </Card>

              <div className="space-y-3">
                <Button className="w-full rounded-full py-6 text-lg font-bold">RUN BACKTEST</Button>
                <Link href="/activation" className="block">
                  <Button
                    variant="outline"
                    className="w-full rounded-full border-primary/30 bg-transparent py-6 text-lg font-bold"
                  >
                    SAVE STRATEGY
                  </Button>
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
