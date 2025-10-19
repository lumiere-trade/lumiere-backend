"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Wallet, CheckCircle2 } from "lucide-react"

export default function OnboardingPage() {
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [showTermsDialog, setShowTermsDialog] = useState(false)
  const [agreedToTerms, setAgreedToTerms] = useState(false)
  const [accountCreated, setAccountCreated] = useState(false)

  const handleConnectWallet = async () => {
    setIsConnecting(true)
    // Simulate wallet connection
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setIsConnected(true)
    setIsConnecting(false)
  }

  const handleCreateAccount = () => {
    setShowTermsDialog(true)
  }

  const handleConfirmTerms = () => {
    if (agreedToTerms) {
      setAccountCreated(true)
      setShowTermsDialog(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto flex min-h-screen flex-col items-center justify-center px-6">
        <Card className="w-full max-w-2xl border-2 border-primary/20 bg-card p-12">
          <div className="text-center">
            <h1 className="mb-4 text-5xl font-bold tracking-tight text-primary">WELCOME TO LUMIERE</h1>
            <p className="mb-12 text-xl text-muted-foreground">
              Connect your Solana wallet to begin forging winning strategies
            </p>

            <div className="mb-8 flex justify-center gap-6">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`flex h-16 w-16 items-center justify-center rounded-full border-2 ${
                    isConnected ? "border-primary bg-primary/20" : "border-muted-foreground/30"
                  }`}
                >
                  {isConnected ? (
                    <CheckCircle2 className="h-8 w-8 text-primary" />
                  ) : (
                    <Wallet className="h-8 w-8 text-muted-foreground" />
                  )}
                </div>
                <span className="text-sm font-medium">Connect Wallet</span>
              </div>

              <div className="flex items-center">
                <div className="h-0.5 w-24 bg-muted-foreground/30" />
              </div>

              <div className="flex flex-col items-center gap-2">
                <div
                  className={`flex h-16 w-16 items-center justify-center rounded-full border-2 ${
                    accountCreated ? "border-primary bg-primary/20" : "border-muted-foreground/30"
                  }`}
                >
                  <CheckCircle2 className={`h-8 w-8 ${accountCreated ? "text-primary" : "text-muted-foreground/30"}`} />
                </div>
                <span className="text-sm font-medium">Create Account</span>
              </div>

              <div className="flex items-center">
                <div className="h-0.5 w-24 bg-muted-foreground/30" />
              </div>

              <div className="flex flex-col items-center gap-2">
                <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-muted-foreground/30">
                  <CheckCircle2 className="h-8 w-8 text-muted-foreground/30" />
                </div>
                <span className="text-sm font-medium">Start Trading</span>
              </div>
            </div>

            {!isConnected ? (
              <div className="space-y-4">
                <Button
                  size="lg"
                  className="w-full rounded-full py-6 text-lg font-bold"
                  onClick={handleConnectWallet}
                  disabled={isConnecting}
                >
                  {isConnecting ? (
                    "CONNECTING..."
                  ) : (
                    <>
                      <Wallet className="mr-2 h-5 w-5" />
                      CONNECT SOLANA WALLET
                    </>
                  )}
                </Button>

                <div className="flex gap-3">
                  <Button variant="outline" size="lg" className="flex-1 rounded-full font-semibold bg-transparent">
                    Phantom
                  </Button>
                  <Button variant="outline" size="lg" className="flex-1 rounded-full font-semibold bg-transparent">
                    Solflare
                  </Button>
                  <Button variant="outline" size="lg" className="flex-1 rounded-full font-semibold bg-transparent">
                    Other
                  </Button>
                </div>
              </div>
            ) : !accountCreated ? (
              <Button size="lg" className="w-full rounded-full py-6 text-lg font-bold" onClick={handleCreateAccount}>
                CREATE ACCOUNT
              </Button>
            ) : (
              <Link href="/architect" className="block w-full">
                <Button size="lg" className="w-full rounded-full py-6 text-lg font-bold">
                  CONTINUE TO ARCHITECT
                </Button>
              </Link>
            )}
          </div>
        </Card>

        <p className="mt-8 text-center text-sm text-muted-foreground">
          By connecting your wallet, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>

      <Dialog open={showTermsDialog} onOpenChange={setShowTermsDialog}>
        <DialogContent className="max-w-2xl bg-[#2a1f1a] border-2 border-primary/30 rounded-2xl shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-primary">Terms of Use & Legal Agreements</DialogTitle>
            <DialogDescription>Please read and agree to our terms before creating your account</DialogDescription>
          </DialogHeader>

          <ScrollArea className="h-[400px] rounded-md border border-primary/20 p-6">
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

          <div className="flex items-center space-x-2 rounded-md border border-primary/20 p-4">
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

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTermsDialog(false)} className="rounded-full">
              Cancel
            </Button>
            <Button onClick={handleConfirmTerms} disabled={!agreedToTerms} className="rounded-full">
              Confirm & Create Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
