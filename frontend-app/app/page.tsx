"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { AdminLoginWall } from "@/components/AdminLoginWall"

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace("/dashboard")
  }, [router])

  return (
    <AdminLoginWall>
      <div className="min-h-screen bg-background" />
    </AdminLoginWall>
  )
}
