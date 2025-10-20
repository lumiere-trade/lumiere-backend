"use client"

import { Button } from "@/components/ui/button"
import Link from "next/link"

export function MarketingHeader() {
  const handleLaunchApp = () => {
    window.location.href = 'http://localhost:3001'
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background shrink-0">
      <div className="container mx-auto flex items-center justify-between px-6 py-4">
        <Link href="/" className="flex flex-col transition-all hover:brightness-110">
          <div className="text-2xl font-bold tracking-wider text-primary">LUMIERE</div>
          <p className="text-[13px] text-muted-foreground tracking-wide">Blind to emotion, guided by algorithm</p>
        </Link>
        <div className="flex items-center gap-3">
          <Link href="/docs">
            <Button variant="outline" size="lg" className="rounded-full px-6 font-semibold bg-transparent">
              DOCS
            </Button>
          </Link>
          <Link href="/learn-more">
            <Button variant="outline" size="lg" className="rounded-full px-6 font-semibold bg-transparent">
              LEARN MORE
            </Button>
          </Link>
          <Link href="/terms">
            <Button variant="outline" size="lg" className="rounded-full px-6 font-semibold bg-transparent">
              LEGAL
            </Button>
          </Link>
          <Button
            variant="default"
            size="lg"
            className="rounded-full px-8 font-semibold"
            onClick={handleLaunchApp}
          >
            LAUNCH APP
          </Button>
        </div>
      </div>
    </header>
  )
}
