"use client"

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Wallet, Copy, DollarSign } from "lucide-react"
import { useWallet } from "@solana/wallet-adapter-react"
import { useAuth } from "@/hooks/use-auth"

interface WalletPanelProps {
  trigger?: React.ReactNode
}

export function WalletPanel({ trigger }: WalletPanelProps) {
  const { user } = useAuth()
  const { disconnect, wallet } = useWallet()

  const walletAddress = user?.walletAddress ? `${user.walletAddress.slice(0, 4)}...${user.walletAddress.slice(-4)}` : "Not connected"
  const walletType = wallet?.adapter.name || "Unknown"

  const mockData = {
    totalBalance: 1193.83,
    depositedFunds: {
      usdc: {
        amount: 500.00,
        value: 500.00,
      },
    },
    walletFunds: {
      usdc: {
        amount: 493.353413,
        value: 493.20,
      },
    },
  }

  const handleCopyAddress = () => {
    if (user?.walletAddress) {
      navigator.clipboard.writeText(user.walletAddress)
    }
  }

  const handleDeposit = () => {
    console.log('Deposit USDC')
  }

  const handleDisconnect = () => {
    disconnect()
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        {trigger || (
          <Button variant="outline" size="lg" className="rounded-full bg-transparent font-semibold gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20">
              <Wallet className="h-4 w-4 text-primary" />
            </div>
            {walletAddress}
          </Button>
        )}
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] bg-background border-l border-primary/20">
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
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={handleCopyAddress}>
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" className="rounded-full bg-transparent" onClick={handleDisconnect}>
                Disconnect
              </Button>
            </div>
          </div>
        </SheetHeader>

        <div className="mt-6 px-2">
          <Tabs defaultValue="balances" className="w-full">
            <TabsList className="grid w-full grid-cols-3 bg-muted/30">
              <TabsTrigger value="balances">Balances</TabsTrigger>
              <TabsTrigger value="positions">Positions</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
            </TabsList>

            <TabsContent value="balances" className="mt-6 space-y-6 px-1">
              <div className="rounded-lg border border-primary/20 bg-card p-6">
                <div className="mb-2 text-sm text-muted-foreground">Total Balance</div>
                <div className="text-4xl font-bold text-primary">${mockData.totalBalance.toFixed(2)}</div>
              </div>

              <div>
                <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Deposited Funds
                </h3>
                <div className="rounded-lg border border-primary/20 bg-card p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
                        <DollarSign className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="font-semibold">USDC</div>
                        <div className="text-sm text-muted-foreground">USD Coin</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{mockData.depositedFunds.usdc.amount.toFixed(2)}</div>
                      <div className="text-sm text-muted-foreground">
                        ${mockData.depositedFunds.usdc.value.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                  Wallet Funds
                </h3>
                <div className="rounded-lg border border-primary/20 bg-card p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
                        <DollarSign className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="font-semibold">USDC</div>
                        <div className="text-sm text-muted-foreground">USD Coin</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="font-semibold">{mockData.walletFunds.usdc.amount.toFixed(6)}</div>
                        <div className="text-sm text-muted-foreground">
                          ${mockData.walletFunds.usdc.value.toFixed(2)}
                        </div>
                      </div>
                      <Button size="sm" className="rounded-full px-6" onClick={handleDeposit}>
                        Deposit
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="positions" className="mt-6 px-1">
              <div className="text-center py-12 text-muted-foreground">
                No active positions
              </div>
            </TabsContent>

            <TabsContent value="activity" className="mt-6 px-1">
              <div className="text-center py-12 text-muted-foreground">
                No recent activity
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </SheetContent>
    </Sheet>
  )
}
