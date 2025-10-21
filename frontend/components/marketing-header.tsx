"use client"

import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import Link from "next/link"
import { Menu } from "lucide-react"

export function MarketingHeader() {
  const handleLaunchApp = () => {
    window.location.href = 'https://app.lumiere.trade'
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

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-3">
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
        </nav>

        {/* Mobile Navigation */}
        <div className="flex md:hidden items-center gap-2">
          <Button
            variant="default"
            size="sm"
            className="rounded-full px-4 font-semibold"
            onClick={handleLaunchApp}
          >
            LAUNCH
          </Button>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="rounded-full">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[280px] bg-background border-l border-primary/20">
              <nav className="flex flex-col gap-4 mt-8">
                <Link href="/docs">
                  <Button variant="outline" size="lg" className="w-full rounded-full font-semibold">
                    DOCS
                  </Button>
                </Link>
                <Link href="/learn-more">
                  <Button variant="outline" size="lg" className="w-full rounded-full font-semibold">
                    LEARN MORE
                  </Button>
                </Link>
                <Link href="/terms">
                  <Button variant="outline" size="lg" className="w-full rounded-full font-semibold">
                    LEGAL
                  </Button>
                </Link>
                <Button
                  variant="default"
                  size="lg"
                  className="w-full rounded-full font-semibold"
                  onClick={handleLaunchApp}
                >
                  LAUNCH APP
                </Button>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
