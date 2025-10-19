import { Button } from "@/components/ui/button"
import Link from "next/link"
import { MessageSquare, TrendingUp, Shield, Brain, Target, Eye, Lock, RefreshCw } from "lucide-react"
import { Footer } from "@/components/footer"

export default function LearnMorePage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto flex items-center justify-between px-6 py-4">
          <Link href="/">
            <div className="flex flex-col cursor-pointer">
              <div className="text-2xl font-bold tracking-wider text-primary">LUMIERE</div>
              <p className="text-xs text-muted-foreground italic tracking-wide">
                Blind to emotion, guided by algorithm
              </p>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/docs">
              <Button variant="outline" size="lg" className="rounded-full px-6 font-semibold bg-transparent">
                DOCS
              </Button>
            </Link>
            <Button variant="default" size="lg" className="rounded-full px-6 font-semibold">
              LEARN MORE
            </Button>
            <Link href="/onboarding">
              <Button variant="outline" size="lg" className="rounded-full px-8 font-semibold bg-transparent">
                CONNECT WALLET
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 pt-32 pb-20 max-w-5xl flex-1">
        {/* Hero Section */}
        <div className="text-center mb-20">
          <h1 className="text-6xl font-bold text-primary mb-6 tracking-wide">
            The Next Generation of AI-Driven Trading
          </h1>
          <p className="text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
            Lumiere transforms how strategies are created, tested, and deployed. Built for traders who value precision
            over emotion, Lumiere uses advanced artificial intelligence to turn market data into adaptive trading models
            that evolve with the markets.
          </p>
        </div>

        {/* How It Works Section */}
        <section className="mb-20">
          <h2 className="text-4xl font-bold text-foreground mb-8">How It Works</h2>
          <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
            Behind every Lumiere strategy stands a multi-layered AI system that combines:
          </p>
          <div className="space-y-6">
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <div className="flex-shrink-0">
                <MessageSquare className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-primary mb-2">Conversational Intelligence</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Talk with Prophet AI, your personal strategy architect. Describe your goals, and it designs trading
                  logic tailored to your style.
                </p>
              </div>
            </div>
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <div className="flex-shrink-0">
                <TrendingUp className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-primary mb-2">Analytical Depth</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Lumiere studies years of historical market data using advanced indicators and mathematical models,
                  identifying unique market patterns invisible to the human eye.
                </p>
              </div>
            </div>
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <div className="flex-shrink-0">
                <Target className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-primary mb-2">Autonomous Execution</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Once deployed, strategies monitor markets in real time, react instantly, and manage trades
                  automatically, with built-in risk and performance tracking.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Why Lumiere Section */}
        <section className="mb-20">
          <h2 className="text-4xl font-bold text-foreground mb-8">Why Lumiere</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <Shield className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-primary mb-2">Emotion-free trading</h3>
                <p className="text-muted-foreground leading-relaxed">Every decision is guided by data, not bias.</p>
              </div>
            </div>
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <Eye className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-primary mb-2">Full transparency</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Real-time insights and detailed performance analytics.
                </p>
              </div>
            </div>
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <RefreshCw className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-primary mb-2">Continuous learning</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Lumiere refines its logic with each cycle, adapting to new conditions and evolving markets.
                </p>
              </div>
            </div>
            <div className="flex gap-4 p-6 rounded-lg border border-primary/20 bg-card/50">
              <Lock className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-primary mb-2">Secure and private</h3>
                <p className="text-muted-foreground leading-relaxed">
                  All strategies and data stay within your control.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Meet Prophet AI Section */}
        <section className="mb-20 p-8 rounded-lg border border-primary/30 bg-card/30">
          <div className="flex items-start gap-6">
            <Brain className="w-12 h-12 text-primary flex-shrink-0" />
            <div>
              <h2 className="text-4xl font-bold text-foreground mb-4">Meet Prophet AI</h2>
              <p className="text-lg text-muted-foreground leading-relaxed mb-4">
                At the heart of Lumiere is Prophet, an advanced AI engine trained to understand trading logic, market
                structures, and human intent. It speaks your language — not just charts.
              </p>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Prophet turns your ideas into structured trading models, backtests them against real data, and prepares
                them for live execution — all in one continuous, intelligent workflow.
              </p>
            </div>
          </div>
        </section>

        {/* The Vision Section */}
        <section className="text-center">
          <h2 className="text-4xl font-bold text-foreground mb-6">The Vision</h2>
          <p className="text-xl text-muted-foreground mb-6 leading-relaxed">Lumiere's mission is simple:</p>
          <p className="text-2xl font-semibold text-primary mb-8">
            To make algorithmic trading accessible, intelligent, and emotionally neutral.
          </p>
          <p className="text-lg text-muted-foreground leading-relaxed max-w-3xl mx-auto mb-12">
            By merging human creativity with machine precision, Lumiere empowers traders to operate at a level once
            reserved for institutions — all through an intuitive AI experience.
          </p>
          <Link href="/onboarding">
            <Button
              size="lg"
              className="rounded-full px-16 py-6 text-xl font-bold transition-all duration-300 hover:brightness-110 hover:ring-2 hover:ring-primary/30"
            >
              GET STARTED
            </Button>
          </Link>
        </section>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  )
}
