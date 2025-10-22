"use client"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link"
import { useState } from "react"
import { Settings, Copy, Wallet, ArrowDownToLine, LogOut } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import { useWallet } from "@solana/wallet-adapter-react"
import { WalletPanel } from "@/components/wallet/WalletPanel"

interface NavigationHeaderProps {
  currentPage?: "dashboard" | "create"
}

export function NavigationHeader({ currentPage }: NavigationHeaderProps) {
  const { user, logout } = useAuth()
  const { disconnect } = useWallet()
  const [depositAmount, setDepositAmount] = useState("")

  const usdcBalance = "993.35"
  const walletAddress = user?.walletAddress ? `${user.walletAddress.slice(0, 4)}...${user.walletAddress.slice(-4)}` : "Not connected"
  const walletType = user?.walletType || "Unknown"

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

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background shrink-0">
      <div className="container mx-auto flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
        <Link href="/" className="flex flex-col transition-all hover:brightness-110">
          <div className="text-xl md:text-2xl font-bold tracking-wider text-primary">LUMIERE</div>
          <p className="text-[11px] md:text-[13px] text-muted-foreground tracking-wide hidden sm:block">
            Blind to emotion, guided by algorithm
          </p>
        </Link>

        <nav className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button
              variant="outline"
              size="lg"
              className="rounded-full px-6 md:px-8 font-semibold"
            >
              DASHBOARD
            </Button>
          </Link>
          <Link href="/create">
            <Button
              variant="outline"
              size="lg"
              className="rounded-full px-6 md:px-8 font-semibold"
            >
              CREATE
            </Button>
          </Link>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="default" size="lg" className="rounded-full px-4 md:px-6 font-semibold gap-2">
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
                className="rounded-full"
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
                    <span className="flex-1 font-mono text-sm">{user?.walletAddress || "Not connected"}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => user?.walletAddress && navigator.clipboard.writeText(user.walletAddress)}
                      disabled={!user?.walletAddress}
                    >
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
                    {user?.createdAt ? user.createdAt.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : "Not available"}
                  </div>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <WalletPanel
            trigger={
              <Button
                variant="outline"
                size="lg"
                className="group rounded-full font-semibold gap-2"
              >
                <span className="isolate">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary-foreground">
                    <Wallet className="h-4 w-4 text-primary" />
                  </div>
                </span>
                {walletAddress}
              </Button>
            }
          />

          <Button
            variant="outline"
            size="icon"
            className="rounded-full"
            onClick={handleDisconnect}
            title="Disconnect Wallet"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </nav>
      </div>
    </header>
  )
}
