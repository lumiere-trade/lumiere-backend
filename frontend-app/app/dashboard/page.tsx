"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { NavigationHeader } from "@/components/navigation-header"
import { WalletConnectionModal } from "@/components/wallet/WalletConnectionModal"
import { useAuth } from "@/hooks/use-auth"
import { TrendingUp, TrendingDown, Activity, DollarSign, Zap, Bell, Pause, Sparkles, Send } from "lucide-react"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"

export default function DashboardPage() {
  const { user } = useAuth()
  const [showWalletModal, setShowWalletModal] = useState(false)

  useEffect(() => {
    setShowWalletModal(!user)
  }, [user])

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to your dashboard! I'm Prophet, your AI trading advisor. I can help you monitor your strategies, analyze performance, and answer questions about your trades.",
    },
  ])
  const [input, setInput] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleSend = () => {
    if (!input.trim()) return

    setMessages([...messages, { role: "user", content: input }])
    setInput("")
    setIsAnalyzing(true)

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Your strategy is performing well! The win rate of 68.5% is above average, and your P&L today shows strong momentum. Would you like me to analyze any specific trades or suggest optimizations?",
        },
      ])
      setIsAnalyzing(false)
    }, 2000)
  }

  const trades = [
    {
      time: "14:32:15",
      pair: "SOL/USDT",
      type: "BUY",
      amount: "2.5 SOL",
      price: "$142.35",
      status: "completed",
    },
    {
      time: "13:15:42",
      pair: "SOL/USDT",
      type: "SELL",
      amount: "2.5 SOL",
      price: "$145.20",
      status: "completed",
    },
    {
      time: "11:48:23",
      pair: "SOL/USDT",
      type: "BUY",
      amount: "2.5 SOL",
      price: "$138.90",
      status: "completed",
    },
  ]

  const portfolioData = [
    { date: "Oct 1", value: 1000 },
    { date: "Oct 2", value: 1050 },
    { date: "Oct 3", value: 1020 },
    { date: "Oct 4", value: 1100 },
    { date: "Oct 5", value: 1150 },
    { date: "Oct 6", value: 1180 },
    { date: "Oct 7", value: 1200 },
    { date: "Oct 8", value: 1248 },
  ]

  const dailyPnLData = [
    { day: "Mon", pnl: 45 },
    { day: "Tue", pnl: -12 },
    { day: "Wed", pnl: 67 },
    { day: "Thu", pnl: 23 },
    { day: "Fri", pnl: 89 },
    { day: "Sat", pnl: 34 },
    { day: "Sun", pnl: 48 },
  ]

  const winLossData = [
    { name: "Wins", value: 87, color: "#d4a574" },
    { name: "Losses", value: 40, color: "#78716c" },
  ]

  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader currentPage="dashboard" />

      {!user && (
        <>
          <div className="fixed inset-0 z-40 backdrop-blur-sm bg-background/30 pointer-events-none" />
          <WalletConnectionModal
            isOpen={showWalletModal}
            onClose={() => setShowWalletModal(false)}
          />
        </>
      )}

      <div className="flex min-h-[calc(100vh-64px)]">
        <div className="flex w-80 flex-col border-r border-border h-[calc(100vh-64px)] sticky top-[64px]">
          <div className="flex flex-1 flex-col">
            <div className="border-b border-border p-4">
              <div className="mb-1 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-bold text-primary">PROPHET AI</h3>
              </div>
              <p className="text-xs text-muted-foreground">Trading Advisor</p>
            </div>

            <div className="flex flex-1 flex-col p-4">
              <div className="mb-3 flex-1 space-y-3 overflow-y-auto rounded-lg border border-border bg-card/30 p-3">
                {messages.map((message, index) => (
                  <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[90%] rounded-xl px-3 py-2 ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "border border-primary/20 bg-card text-foreground"
                      }`}
                    >
                      {message.role === "assistant" && (
                        <div className="mb-1 flex items-center gap-1 text-xs text-primary">
                          <Sparkles className="h-3 w-3" />
                          <span className="font-semibold">Prophet</span>
                        </div>
                      )}
                      <p className="text-xs leading-relaxed">{message.content}</p>
                    </div>
                  </div>
                ))}
                {isAnalyzing && (
                  <div className="flex justify-start">
                    <div className="max-w-[90%] rounded-xl border border-primary/20 bg-card px-3 py-2">
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
          </div>
        </div>

        <div className="flex-1">
          <div className="container mx-auto px-6 py-6">
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h1 className="mb-2 text-5xl font-bold tracking-tight text-primary">LIVE TRADING</h1>
                <p className="text-lg text-muted-foreground">
                  Strategy: SOL/USDT Momentum • Status: <span className="text-primary">Active</span>
                </p>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" size="lg" className="rounded-full bg-transparent">
                  <Pause className="mr-2 h-5 w-5" />
                  PAUSE
                </Button>
                <Button variant="destructive" size="lg" className="rounded-full">
                  STOP STRATEGY
                </Button>
              </div>
            </div>

            <div className="mb-8 grid gap-6 md:grid-cols-4">
              <Card className="border-primary/20 p-6">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Balance</span>
                  <DollarSign className="h-5 w-5 text-primary" />
                </div>
                <div className="text-3xl font-bold">$1,247.82</div>
                <div className="mt-1 flex items-center gap-1 text-sm text-green-500">
                  <TrendingUp className="h-4 w-4" />
                  <span>+24.78% (24h)</span>
                </div>
              </Card>

              <Card className="border-primary/20 p-6">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Trades</span>
                  <Activity className="h-5 w-5 text-primary" />
                </div>
                <div className="text-3xl font-bold">127</div>
                <div className="mt-1 text-sm text-muted-foreground">Win Rate: 68.5%</div>
              </Card>

              <Card className="border-primary/20 p-6">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Today's P&L</span>
                  <TrendingUp className="h-5 w-5 text-green-500" />
                </div>
                <div className="text-3xl font-bold text-green-500">+$47.82</div>
                <div className="mt-1 text-sm text-muted-foreground">8 trades executed</div>
              </Card>

              <Card className="border-primary/20 p-6">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Active Since</span>
                  <Zap className="h-5 w-5 text-primary" />
                </div>
                <div className="text-3xl font-bold">7d 14h</div>
                <div className="mt-1 text-sm text-muted-foreground">Uptime: 99.8%</div>
              </Card>
            </div>

            <div className="mb-8 grid gap-6 lg:grid-cols-3">
              <Card className="lg:col-span-2 border-primary/20 p-6">
                <div className="mb-4 border-b border-border pb-4">
                  <h2 className="text-xl font-bold">Portfolio Value</h2>
                  <p className="text-sm text-muted-foreground">Last 7 days performance</p>
                </div>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={portfolioData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" style={{ fontSize: "12px" }} />
                    <YAxis stroke="hsl(var(--muted-foreground))" style={{ fontSize: "12px" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="hsl(var(--primary))"
                      strokeWidth={3}
                      dot={{ fill: "hsl(var(--primary))" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>

              <Card className="border-primary/20 p-6">
                <div className="mb-4 border-b border-border pb-4">
                  <h2 className="text-xl font-bold">Win Rate</h2>
                  <p className="text-sm text-muted-foreground">Trade distribution</p>
                </div>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={winLossData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {winLossData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </div>

            <Card className="mb-8 border-primary/20 p-6">
              <div className="mb-4 border-b border-border pb-4">
                <h2 className="text-xl font-bold">Daily P&L</h2>
                <p className="text-sm text-muted-foreground">Profit and loss by day</p>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={dailyPnLData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" style={{ fontSize: "12px" }} />
                  <YAxis stroke="hsl(var(--muted-foreground))" style={{ fontSize: "12px" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="pnl" radius={[8, 8, 0, 0]}>
                    {dailyPnLData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "#d4a574" : "#ef4444"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <div className="grid gap-6 lg:grid-cols-3">
              <Card className="lg:col-span-2 border-primary/20 p-6">
                <div className="mb-4 flex items-center justify-between border-b border-border pb-4">
                  <h2 className="text-xl font-bold">Recent Trades</h2>
                  <Button variant="outline" size="sm" className="rounded-full bg-transparent">
                    View All
                  </Button>
                </div>

                <div className="space-y-3">
                  {trades.map((trade, index) => (
                    <div key={index} className="flex items-center justify-between rounded-lg bg-muted/50 p-4">
                      <div className="flex items-center gap-4">
                        <div
                          className={`flex h-10 w-10 items-center justify-center rounded-full ${
                            trade.type === "BUY" ? "bg-green-500/20" : "bg-red-500/20"
                          }`}
                        >
                          {trade.type === "BUY" ? (
                            <TrendingUp className="h-5 w-5 text-green-500" />
                          ) : (
                            <TrendingDown className="h-5 w-5 text-red-500" />
                          )}
                        </div>
                        <div>
                          <div className="font-semibold">{trade.pair}</div>
                          <div className="text-sm text-muted-foreground">{trade.time}</div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-semibold">{trade.amount}</div>
                        <div className="text-sm text-muted-foreground">@ {trade.price}</div>
                      </div>

                      <div
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          trade.type === "BUY" ? "bg-green-500/20 text-green-500" : "bg-red-500/20 text-red-500"
                        }`}
                      >
                        {trade.type}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <div className="space-y-6">
                <Card className="border-primary/20 p-6">
                  <div className="mb-4 flex items-center gap-2 border-b border-border pb-4">
                    <Bell className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">Recent Notifications</h3>
                  </div>

                  <div className="space-y-3">
                    {[
                      {
                        time: "2m ago",
                        message: "Buy signal detected for SOL/USDT",
                        type: "info",
                      },
                      {
                        time: "15m ago",
                        message: "Trade executed: +$7.12 profit",
                        type: "success",
                      },
                      {
                        time: "1h ago",
                        message: "Strategy rebalanced successfully",
                        type: "info",
                      },
                    ].map((notif, index) => (
                      <div key={index} className="rounded-lg border border-border p-3">
                        <div className="mb-1 text-xs text-muted-foreground">{notif.time}</div>
                        <div className="text-sm">{notif.message}</div>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="border-primary/20 p-6">
                  <h3 className="mb-4 font-semibold">System Status</h3>
                  <div className="space-y-3 text-sm">
                    {[
                      { name: "Chevalier", status: "Running" },
                      { name: "Chronicler", status: "Running" },
                      { name: "Courier", status: "Running" },
                      { name: "Smart Contract", status: "Connected" },
                    ].map((service) => (
                      <div key={service.name} className="flex items-center justify-between">
                        <span className="text-muted-foreground">{service.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-2 rounded-full bg-green-500" />
                          <span className="font-medium">{service.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
