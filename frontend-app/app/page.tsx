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
      router.push(ROUTES.DASHBOARD)
    } else {
      setShowWalletModal(true)
    }
  }, [user, isLoading, router])

  return (
    <div className="min-h-screen bg-background">
      {showWalletModal && (
        <WalletConnectionModal
          isOpen={showWalletModal}
          onClose={() => {
            setShowWalletModal(false)
          }}
        />
      )}
    </div>
  )
}
