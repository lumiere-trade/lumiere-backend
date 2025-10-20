"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/use-auth"
import { WalletConnectionModal } from "@/components/wallet/WalletConnectionModal"
import { ROUTES } from "@/config/constants"

export default function RootPage() {
  const { user, isLoading } = useAuth()
  const [showWalletModal, setShowWalletModal] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (isLoading) return

    if (user) {
      // User authenticated, redirect to dashboard
      router.push(ROUTES.DASHBOARD)
    } else {
      // Not authenticated, show wallet modal immediately
      setShowWalletModal(true)
    }
  }, [user, isLoading, router])

  // Show wallet modal with darkened backdrop
  return (
    <div className="min-h-screen bg-background">
      {showWalletModal && (
        <WalletConnectionModal 
          isOpen={showWalletModal} 
          onClose={() => {
            // User closed modal without connecting - redirect to marketing site
            window.location.href = 'http://localhost:3000'
          }} 
        />
      )}
    </div>
  )
}
