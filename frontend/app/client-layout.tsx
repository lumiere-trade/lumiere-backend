"use client"

import type React from "react"

import { Suspense } from "react"
import { Analytics } from "@vercel/analytics/next"
import { useSearchParams } from "next/navigation"

export function ClientLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const isProduction = process.env.NODE_ENV === "production"
  const searchParams = useSearchParams()

  return (
    <>
      <Suspense fallback={<div>Loading...</div>}>{children}</Suspense>
      {isProduction && <Analytics />}
    </>
  )
}
