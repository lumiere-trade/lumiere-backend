"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { X, Settings, ChevronDown, Ghost, Sun, Backpack, Gem, Zap, Circle, Shield, Wallet, Loader2, ExternalLink } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import { useWallet } from "@/hooks/use-wallet"
import { useWallet as useSolanaWallet } from "@solana/wallet-adapter-react"
import { useRouter } from "next/navigation"
import { ROUTES, AUTH_CONFIG } from "@/config/constants"
import { container } from "@/lib/infrastructure/di/container"
import type React from "react"
import bs58 from "bs58"
import { marked } from "marked"

type WalletOption = {
  icon: React.ComponentType<{ className?: string }>
  recent?: boolean
  installUrl?: string
}

interface WalletConnectionModalProps {
  isOpen: boolean
  onClose: () => void
}

export function WalletConnectionModal({ isOpen, onClose }: WalletConnectionModalProps) {
  const [showRpcSettings, setShowRpcSettings] = useState(false)
  const [selectedRpc, setSelectedRpc] = useState<"triton" | "syndica" | "custom">("triton")
  const [customRpc, setCustomRpc] = useState("")
  const [showAllWallets, setShowAllWallets] = useState(false)
  const [showTermsDialog, setShowTermsDialog] = useState(false)
  const [agreedToTerms, setAgreedToTerms] = useState(false)
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [localError, setError] = useState<string | null>(null)
  const [connectedWalletAddress, setConnectedWalletAddress] = useState<string | null>(null)

  const { login, createAccount, legalDocuments, loadLegalDocuments, error: authError } = useAuth()
  const { error: walletError, disconnect } = useWallet()
  const solanaWallet = useSolanaWallet()
  const router = useRouter()

  const initialWallets: WalletOption[] = [
    { name: "Phantom", icon: Ghost, recent: true, installUrl: "https://phantom.app/download" },
    { name: "Solflare", icon: Sun, recent: false, installUrl: "https://solflare.com/download" },
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

  const handleWalletClick = async (wallet: WalletOption) => {
    setSelectedWallet(wallet.name)
    setIsProcessing(true)
    setError(null)

    try {
      console.log(`[Wallet] Attempting to connect: ${wallet.name}`)

      if (wallet.name === 'Phantom' && typeof window !== 'undefined') {
        const provider = (window as any).phantom?.solana

        if (!provider?.isPhantom) {
          if (wallet.installUrl) {
            window.open(wallet.installUrl, '_blank')
            setError('Please install Phantom wallet first')
          }
          setIsProcessing(false)
          return
        }

        console.log('[Wallet] Phantom provider found')

        if (provider.isConnected && provider.publicKey) {
          console.log('[Wallet] Phantom already connected')
          const walletAddress = provider.publicKey.toString()
          setConnectedWalletAddress(walletAddress)

          const walletAdapter = solanaWallet.wallets.find(
            w => w.adapter.name.toLowerCase() === 'phantom'
          )
          if (walletAdapter) {
            solanaWallet.select(walletAdapter.adapter.name)
          }

          await authenticateWithBackend(walletAddress)
          return
        }

        console.log('[Wallet] Requesting Phantom connection...')

        try {
          const resp = await provider.connect({ onlyIfTrusted: false })
          const walletAddress = resp.publicKey.toString()
          console.log('[Wallet] Phantom connected:', walletAddress)
          setConnectedWalletAddress(walletAddress)

          const walletAdapter = solanaWallet.wallets.find(
            w => w.adapter.name.toLowerCase() === 'phantom'
          )

          if (walletAdapter) {
            console.log('[Wallet] Syncing with wallet adapter...')
            solanaWallet.select(walletAdapter.adapter.name)

            let attempts = 0
            while (!solanaWallet.connected && attempts < 20) {
              await new Promise(resolve => setTimeout(resolve, 100))
              attempts++
            }
          }

          await authenticateWithBackend(walletAddress)

        } catch (connectError: any) {
          console.error('[Wallet] Phantom connection failed:', connectError)

          if (connectError.code === 4001 || connectError.message?.includes('User rejected')) {
            setError('Connection rejected. Please try again.')
          } else {
            setError(connectError.message || 'Failed to connect. Please try again.')
          }
        }
      } else {
        const walletAdapter = solanaWallet.wallets.find(
          w => w.adapter.name.toLowerCase() === wallet.name.toLowerCase()
        )

        if (!walletAdapter) {
          if (wallet.installUrl) {
            window.open(wallet.installUrl, '_blank')
            setError(`Please install ${wallet.name} wallet first`)
          } else {
            setError(`${wallet.name} wallet is not available`)
          }
          setIsProcessing(false)
          return
        }

        console.log('[Wallet] Selecting adapter...')
        solanaWallet.select(walletAdapter.adapter.name)

        console.log('[Wallet] Waiting for wallet initialization...')
        let attempts = 0
        const maxAttempts = 30
        while (!solanaWallet.wallet && attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 100))
          attempts++
        }

        if (!solanaWallet.wallet) {
          throw new Error('Wallet failed to initialize. Please try again.')
        }

        console.log('[Wallet] Requesting connection...')
        await solanaWallet.connect()

        console.log('[Wallet] Connection successful')
        await new Promise(resolve => setTimeout(resolve, 500))

        const walletAddress = solanaWallet.publicKey?.toString()
        if (walletAddress) {
          setConnectedWalletAddress(walletAddress)
          await authenticateWithBackend(walletAddress)
        }
      }
    } catch (error: any) {
      console.error('[Wallet] Connection error:', error)

      if (error.message?.includes('User rejected') || error.code === 4001) {
        setError('Connection rejected. Please try again.')
      } else {
        setError(error.message || 'Failed to connect wallet. Please try again.')
      }
    } finally {
      setIsProcessing(false)
    }
  }

  const authenticateWithBackend = async (walletAddress: string) => {
    console.log('[Auth] Authenticating with backend, wallet:', walletAddress)

    try {
      const provider = (window as any).phantom?.solana
      if (!provider) {
        throw new Error('Wallet provider not available')
      }

      const message = AUTH_CONFIG.MESSAGE
      console.log('[Auth] Requesting signature for message:', message)

      const encodedMessage = new TextEncoder().encode(message)
      const signedMessage = await provider.signMessage(encodedMessage)
      const signature = bs58.encode(signedMessage.signature)

      console.log('[Auth] Signature obtained, calling backend...')

      const authRepository = container.authRepository

      try {
        const verifyResult = await authRepository.verifyWallet(
          walletAddress,
          message,
          signature
        )

        console.log('[Auth] Verify result:', verifyResult)

        if (!verifyResult.userExists) {
          console.log('[Auth] User not found, loading legal documents...')
          await loadLegalDocuments()
          setShowTermsDialog(true)
          return
        }

        console.log('[Auth] User exists, logging in...')
        const loginResult = await authRepository.login(
          walletAddress,
          message,
          signature
        )

        console.log('[Auth] Login successful!')
        container.updateAuthToken(loginResult.accessToken)

        onClose()
        router.push(ROUTES.DASHBOARD)

      } catch (authError: any) {
        console.error('[Auth] Authentication error:', authError)

        if (authError.message?.includes('not found')) {
          await loadLegalDocuments()
          setShowTermsDialog(true)
        } else {
          setError(authError.message || 'Authentication failed')
        }
      }

    } catch (error: any) {
      console.error('[Auth] Backend authentication failed:', error)
      setError(error.message || 'Authentication failed')
    }
  }

  const handleConfirmTerms = async () => {
    if (!agreedToTerms || !connectedWalletAddress) return

    setIsProcessing(true)
    setError(null)

    try {
      console.log('[Account] Creating account for wallet:', connectedWalletAddress)

      const provider = (window as any).phantom?.solana
      if (!provider) {
        throw new Error('Wallet provider not available')
      }

      const message = AUTH_CONFIG.MESSAGE
      const encodedMessage = new TextEncoder().encode(message)
      const signedMessage = await provider.signMessage(encodedMessage)
      const signature = bs58.encode(signedMessage.signature)

      const documentIds = legalDocuments.map(doc => doc.id)
      console.log('[Account] Calling create-account API...')

      const authRepository = container.authRepository
      const result = await authRepository.createAccount(
        connectedWalletAddress,
        message,
        signature,
        documentIds
      )

      console.log('[Account] Account created successfully!')
      container.updateAuthToken(result.accessToken)

      setShowTermsDialog(false)
      onClose()
      router.push(ROUTES.CREATE)
    } catch (error: any) {
      console.error('[Account] Account creation error:', error)
      setError(error.message || 'Account creation failed')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCancelTerms = () => {
    setShowTermsDialog(false)
    setAgreedToTerms(false)
    setConnectedWalletAddress(null)
    disconnect()
  }

  const termsDoc = legalDocuments.find(doc => doc.documentType === 'terms_of_service')

  if (showTermsDialog) {
    return (
      <Dialog open={showTermsDialog} onOpenChange={handleCancelTerms}>
        <DialogContent className="max-w-2xl bg-background border-2 border-primary/30 rounded-2xl shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-primary">Terms of Use & Legal Agreements</DialogTitle>
          </DialogHeader>

          <ScrollArea className="h-[400px] rounded-md border border-primary/20 bg-card/30 p-6">
            <div className="space-y-6 text-sm prose prose-invert prose-sm max-w-none">
              {termsDoc ? (
                <div dangerouslySetInnerHTML={{ __html: marked.parse(termsDoc.content) }} />
              ) : (
                <div className="space-y-6">
                  <section>
                    <h3 className="mb-2 text-lg font-semibold text-primary">1. Acceptance of Terms</h3>
                    <p className="text-muted-foreground">
                      By accessing and using LUMIERE, you accept and agree to be bound by the terms and provision of this
                      agreement.
                    </p>
                  </section>
                  <section>
                    <h3 className="mb-2 text-lg font-semibold text-primary">2. Trading Risks</h3>
                    <p className="text-muted-foreground">
                      Trading cryptocurrencies involves substantial risk of loss. Past performance does not guarantee future results.
                    </p>
                  </section>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="flex items-center space-x-2 rounded-md border border-primary/20 bg-card/30 p-4">
            <Checkbox
              id="terms"
              checked={agreedToTerms}
              onCheckedChange={(checked) => setAgreedToTerms(checked as boolean)}
              disabled={isProcessing}
            />
            <label htmlFor="terms" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              I have read and agree to the Terms of Use and Legal Agreements
            </label>
          </div>

          {(authError || localError) && (
            <div className="text-sm text-red-500 text-center p-2 bg-red-500/10 rounded-lg border border-red-500/20">
              {localError || authError}
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={handleCancelTerms} className="rounded-full" disabled={isProcessing}>
              Cancel
            </Button>
            <Button onClick={handleConfirmTerms} disabled={!agreedToTerms || isProcessing} className="rounded-full">
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Account...
                </>
              ) : (
                'Confirm & Continue'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (showRpcSettings) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowRpcSettings(false)}>
        <div className="relative w-full max-w-lg mx-4 bg-background rounded-2xl border-2 border-primary/30 shadow-2xl" onClick={(e) => e.stopPropagation()}>
          <button onClick={() => setShowRpcSettings(false)} className="absolute top-6 left-6 text-muted-foreground hover:text-primary transition-colors">
            <X className="h-5 w-5" />
          </button>

          <div className="p-8 space-y-6">
            <div className="text-center">
              <h1 className="text-3xl font-bold tracking-tight text-primary">Settings</h1>
            </div>

            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-foreground">RPC Endpoint</h2>

              <button onClick={() => setSelectedRpc("triton")} className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${selectedRpc === "triton" ? "bg-card/70 border-primary" : "bg-card/50 border-primary/20 hover:border-primary/30"}`}>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${selectedRpc === "triton" ? "border-primary" : "border-muted-foreground/30"}`}>
                  {selectedRpc === "triton" && <div className="w-3 h-3 rounded-full bg-primary" />}
                </div>
                <span className="text-base font-medium text-foreground">Mainnet Beta (Triton)</span>
              </button>

              <button onClick={() => setSelectedRpc("syndica")} className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${selectedRpc === "syndica" ? "bg-card/70 border-primary" : "bg-card/50 border-primary/20 hover:border-primary/30"}`}>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${selectedRpc === "syndica" ? "border-primary" : "border-muted-foreground/30"}`}>
                  {selectedRpc === "syndica" && <div className="w-3 h-3 rounded-full bg-primary" />}
                </div>
                <span className="text-base font-medium text-foreground">Syndica</span>
              </button>

              <button onClick={() => setSelectedRpc("custom")} className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${selectedRpc === "custom" ? "bg-card/70 border-primary" : "bg-card/50 border-primary/20 hover:border-primary/30"}`}>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${selectedRpc === "custom" ? "border-primary" : "border-muted-foreground/30"}`}>
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
                  className="w-full p-4 rounded-xl bg-card/50 border border-primary/20 focus:border-primary focus:outline-none text-foreground placeholder:text-muted-foreground"
                />
              )}
            </div>

            <Button onClick={() => setShowRpcSettings(false)} className="w-full rounded-full py-6 text-lg font-bold bg-primary hover:bg-primary/90 text-black">
              Save Settings
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => !isProcessing && onClose()}>
      <div className="relative w-full max-w-lg max-h-[90vh] mx-4 bg-background rounded-2xl border-2 border-primary/30 shadow-2xl flex flex-col" onClick={(e) => e.stopPropagation()}>
        <button onClick={() => !isProcessing && onClose()} className="absolute top-6 right-6 text-muted-foreground hover:text-primary transition-colors z-10" disabled={isProcessing}>
          <X className="h-5 w-5" />
        </button>

        <button onClick={() => setShowRpcSettings(true)} className="absolute top-6 right-16 text-muted-foreground hover:text-primary transition-colors z-10">
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
                  const isInstalled = solanaWallet.wallets.some(
                    w => w.adapter.name.toLowerCase() === wallet.name.toLowerCase()
                  )

                  return (
                    <button
                      key={wallet.name}
                      onClick={() => handleWalletClick(wallet)}
                      disabled={isProcessing}
                      className="w-full flex items-center justify-between p-4 rounded-xl bg-card/50 border border-primary/20 hover:border-primary/30 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex items-center gap-4">
                        <div className="rounded-lg bg-primary/10 p-2">
                          <IconComponent className="w-6 h-6 text-primary" />
                        </div>
                        <span className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                          {wallet.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {!isInstalled && wallet.installUrl && (
                          <ExternalLink className="h-4 w-4 text-muted-foreground" />
                        )}
                        {wallet.recent && (
                          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-primary/20 text-primary border border-primary/30">
                            Recent
                          </span>
                        )}
                        {isProcessing && selectedWallet === wallet.name && (
                          <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            </ScrollArea>
          </div>

          {(walletError || authError || localError) && (
            <div className="flex-shrink-0 text-sm text-red-500 text-center p-3 bg-red-500/10 rounded-lg border border-red-500/20">
              {localError || walletError || authError}
            </div>
          )}

          {!showAllWallets && (
            <button
              onClick={() => setShowAllWallets(true)}
              className="w-full flex items-center justify-center gap-2 py-3 text-primary hover:text-primary/80 transition-colors font-semibold flex-shrink-0"
              disabled={isProcessing}
            >
              <ChevronDown className="h-5 w-5" />
              <span>All Wallets</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
