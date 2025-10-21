"use client"

import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link"
import { useState } from "react"
import { Settings, Copy, Wallet, TrendingUp, Activity, ArrowDownToLine } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import { useWallet } from "@solana/wallet-adapter-react"

interface NavigationHeaderProps {
  currentPage?: "dashboard" | "create"
}

export function NavigationHeader({ currentPage }: NavigationHeaderProps) {
  const { user, logout } = useAuth()
  const { disconnect } = useWallet()
  const [depositAmount, setDepositAmount] = useState("")

  const usdcBalance = "993.35"
  const walletAddress = user?.shortAddress || "Not connected"
  const walletType = "phantom"

  const balances = [
    { symbol: "USDC", name: "USD Coin", amount: "993.353413", value: "$993.20", icon: "💵" },
    { symbol: "SOL", name: "Solana", amount: "0.999992001", value: "$200.61", icon: "◎" },
  ]

  const positions = [
    { strategy: "SOL/USDT Momentum", pnl: "+$47.82", status: "Active", color: "text-green-500" },
    { strategy: "BTC Range Trading", pnl: "-$12.30", status: "Paused", color: "text-red-500" },
  ]

  const activities = [
    { time: "14:32:15", action: "Buy 2.5 SOL", price: "$142.35" },
    { time: "13:15:42", action: "Sell 2.5 SOL", price: "$145.20" },
    { time: "11:48:23", action: "Buy 2.5 SOL", price: "$138.90" },
  ]

  const handleDisconnect = async () => {
    try {
      await disconnect()
      logout()
    } catch (error) {
      console.error('Disconnect error:', error)
      logout()
    }
  }

  const handleDeposit = () => {
    console.log(`Depositing ${depositAmount} USDC`)
    setDepositAmount("")
  }

  const handleMaxClick = () => {
    setDepositAmount(usdcBalance)
  }

  if (!user) return null

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto flex items-center justify-between px-6 py-4">
        <Link href="/" className="text-2xl font-bold tracking-wider text-primary hover:opacity-80 transition-opacity">
          LUMIERE
        </Link>

        <nav className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button
              variant="outline"
              size="lg"
              className={`rounded-full px-8 font-semibold transition-all ${
                currentPage === "dashboard" 
                  ? "bg-primary text-primary-foreground border-primary hover:bg-primary/90" 
                  : "bg-transparent hover:bg-primary/10"
              }`}
            >
              DASHBOARD
            </Button>
          </Link>
          <Link href="/architect">
            <Button
              variant="outline"
              size="lg"
              className={`rounded-full px-8 font-semibold transition-all ${
                currentPage === "create" 
                  ? "bg-primary text-primary-foreground border-primary hover:bg-primary/90" 
                  : "bg-transparent hover:bg-primary/10"
              }`}
            >
              CREATE
            </Button>
          </Link>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="default" size="lg" className="rounded-full px-6 font-semibold gap-2">
                <ArrowDownToLine className="h-4 w-4" />
                DEPOSIT
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md bg-[#2a1f1a] border-2 border-primary/30 rounded-2xl shadow-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-primary">Deposit Funds</DialogTitle>
              </DialogHeader>
              <div className="space-y-6 py-4">
                <div className="space-y-2">
                  <Label htmlFor="amount" className="text-sm font-semibold text-muted-foreground">
                    Amount (USDC)
                  </Label>
                  <div className="relative">
                    <Input
                      id="amount"
                      type="number"
                      placeholder="0.00"
                      value={depositAmount}
                      onChange={(e) => setDepositAmount(e.target.value)}
                      className="pr-20 rounded-lg border-primary/30 bg-card text-lg [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleMaxClick}
                      className="absolute right-2 top-1/2 -translate-y-1/2 h-8 rounded-md bg-primary/20 hover:bg-primary/30 font-semibold text-primary"
                    >
                      MAX
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Available: <span className="font-semibold text-primary">{usdcBalance} USDC</span>
                  </p>
                </div>

                <div className="rounded-lg border border-primary/20 bg-card/50 p-4">
                  <div className="mb-2 text-sm text-muted-foreground">Deposit Summary</div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">You will deposit</span>
                    <span className="font-semibold text-primary">{depositAmount || "0.00"} USDC</span>
                  </div>
                </div>

                <Button
                  onClick={handleDeposit}
                  disabled={!depositAmount || Number.parseFloat(depositAmount) <= 0}
                  className="w-full rounded-full py-6 text-lg font-semibold"
                >
                  CONFIRM DEPOSIT
                </Button>

                <p className="text-center text-xs text-muted-foreground">
                  Deposits are processed instantly. Gas fees may apply.
                </p>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog>
            <DialogTrigger asChild>
              <Button 
                variant="outline" 
                size="icon" 
                className="rounded-full bg-transparent hover:bg-primary/10"
              >
                <Settings className="h-5 w-5" />
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md bg-[#2a1f1a] border-2 border-primary/30 rounded-2xl shadow-2xl">
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-primary">User Profile</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-muted-foreground">Wallet Address</label>
                  <div className="flex items-center gap-2 rounded-lg border border-border bg-card p-3">
                    <span className="flex-1 font-mono text-sm">{user.walletAddress}</span>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigator.clipboard.writeText(user.walletAddress)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-muted-foreground">Wallet Type</label>
                  <div className="rounded-lg border border-border bg-card p-3 capitalize">{walletType}</div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-muted-foreground">Member Since</label>
                  <div className="rounded-lg border border-border bg-card p-3">
                    {user.createdAt.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Sheet>
            <SheetTrigger asChild>
              <Button 
                variant="outline" 
                size="lg" 
                className="rounded-full bg-transparent font-semibold gap-2 hover:bg-primary/10"
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20">
                  <Wallet className="h-4 w-4 text-primary" />
                </div>
                {walletAddress}
              </Button>
            </SheetTrigger>
            <SheetContent className="w-[400px] sm:w-[540px] bg-background border-l border-primary/20 [&>button]:hidden">
              <SheetHeader className="border-b border-border pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
                      <Wallet className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <SheetTitle className="text-xl font-bold">{walletAddress}</SheetTitle>
                      <p className="text-sm text-muted-foreground capitalize">{walletType} Wallet</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-full bg-transparent hover:bg-primary/10"
                    onClick={handleDisconnect}
                  >
                    Disconnect
                  </Button>
                </div>
              </SheetHeader>

              <div className="mt-6">
                <Tabs defaultValue="balances" className="w-full">
                  <TabsList className="grid w-full grid-cols-3 bg-muted/30">
                    <TabsTrigger value="balances">Balances</TabsTrigger>
                    <TabsTrigger value="positions">Positions</TabsTrigger>
                    <TabsTrigger value="activity">Activity</TabsTrigger>
                  </TabsList>

                  <TabsContent value="balances" className="mt-6 space-y-4">
                    <div className="rounded-lg border border-primary/20 bg-card p-6">
                      <div className="mb-2 text-sm text-muted-foreground">Total Balance</div>
                      <div className="text-4xl font-bold text-primary">$1,193.83</div>
                    </div>

                    <div className="space-y-3">
                      {balances.map((balance) => (
                        <div
                          key={balance.symbol}
                          className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20 text-xl">
                              {balance.icon}
                            </div>
                            <div>
                              <div className="font-semibold">{balance.symbol}</div>
                              <div className="text-sm text-muted-foreground">{balance.name}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-semibold">{balance.amount}</div>
                            <div className="text-sm text-muted-foreground">{balance.value}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="positions" className="mt-6 space-y-3">
                    {positions.map((position, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
                            <TrendingUp className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <div className="font-semibold">{position.strategy}</div>
                            <div className="text-sm text-muted-foreground">{position.status}</div>
                          </div>
                        </div>
                        <div className={`text-right font-semibold ${position.color}`}>{position.pnl}</div>
                      </div>
                    ))}
                  </TabsContent>

                  <TabsContent value="activity" className="mt-6 space-y-3">
                    {activities.map((activity, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
                            <Activity className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <div className="font-semibold">{activity.action}</div>
                            <div className="text-sm text-muted-foreground">{activity.time}</div>
                          </div>
                        </div>
                        <div className="text-right font-semibold">{activity.price}</div>
                      </div>
                    ))}
                  </TabsContent>
                </Tabs>
              </div>
            </SheetContent>
          </Sheet>
        </nav>
      </div>
    </header>
  )
}
