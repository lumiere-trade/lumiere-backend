"use client"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Settings, Copy, ArrowDownToLine } from "lucide-react"
import { WalletPanel } from "@/components/wallet/WalletPanel"

interface NavigationHeaderProps {
  currentPage?: "dashboard" | "create"
}

export function NavigationHeader({ currentPage }: NavigationHeaderProps) {
  const router = useRouter()
  const [isWalletConnected, setIsWalletConnected] = useState(true)
  const [walletAddress] = useState("kshy...KR2y")
  const [walletType] = useState("phantom")

  const [depositAmount, setDepositAmount] = useState("")

  const usdcBalance = "993.35"

  const handleDisconnect = () => {
    setIsWalletConnected(false)
    router.push("/")
  }

  const handleDeposit = () => {
    console.log(`Depositing ${depositAmount} USDC`)
    setDepositAmount("")
  }

  const handleMaxClick = () => {
    setDepositAmount(usdcBalance)
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto flex items-center justify-between px-6 py-4">
        <Link href="/" className="text-2xl font-bold tracking-wider text-primary hover:opacity-80 transition-opacity">
          LUMIERE
        </Link>

        <nav className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button
              variant={currentPage === "dashboard" ? "default" : "outline"}
              size="lg"
              className="rounded-full px-8 font-semibold bg-transparent"
            >
              DASHBOARD
            </Button>
          </Link>
          <Link href="/create">
            <Button
              variant={currentPage === "create" ? "default" : "outline"}
              size="lg"
              className="rounded-full px-8 font-semibold bg-transparent"
            >
              CREATE
            </Button>
          </Link>

          {isWalletConnected && (
            <>
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
                  <Button variant="outline" size="icon" className="rounded-full bg-transparent">
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
                        <span className="flex-1 font-mono text-sm">{walletAddress}</span>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
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
                      <div className="rounded-lg border border-border bg-card p-3">October 15, 2025</div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-semibold text-muted-foreground">Total Strategies</label>
                      <div className="rounded-lg border border-border bg-card p-3">3 Active Strategies</div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>

              <WalletPanel />
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
