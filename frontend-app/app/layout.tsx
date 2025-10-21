import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "@/providers/providers"
import { AdminAuthProvider } from "@/contexts/AdminAuthContext"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Lumiere - Algorithmic Trading Platform",
  description: "Blind to emotion, guided by algorithm",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <AdminAuthProvider>
          <Providers>{children}</Providers>
        </AdminAuthProvider>
      </body>
    </html>
  )
}
