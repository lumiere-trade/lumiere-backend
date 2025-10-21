"use client";

import { MarketingHeader } from "@/components/marketing-header";
import { Footer } from "@/components/footer";
import { AdminLoginWall } from "@/components/admin-login-wall";

export default function Home() {
  return (
    <AdminLoginWall>
      <div className="flex min-h-screen flex-col bg-[#1a1410]">
        <MarketingHeader />
        <main className="flex-1">
          <section className="relative overflow-hidden py-32">
            <div className="container mx-auto px-4">
              <div className="mx-auto max-w-4xl text-center">
                <h1 className="mb-6 text-6xl font-bold tracking-tight text-[#d4a574]">
                  LUMIERE
                </h1>
                <p className="mb-8 text-2xl text-[#a0826d]">
                  AI-Powered Trading Strategy Platform
                </p>
                <p className="mb-12 text-lg text-[#a0826d]/80">
                  Transform raw market data into winning strategies with the power of AI. Lumiere combines
                  advanced market analysis, intelligent backtesting, and automated deployment to help you
                  trade smarter, not harder.
                </p>
                <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                  
                    <a href="https://app.lumiere.trade"
                    className="inline-flex items-center justify-center rounded-full bg-[#d4a574] px-8 py-4 text-lg font-bold text-black transition-colors hover:bg-[#c49564]"
                  >
                    START TRADING
                  </a>
                </div>
              </div>
            </div>
          </section>

          <section className="py-20">
            <div className="container mx-auto px-4">
              <div className="grid gap-8 md:grid-cols-3">
                <div className="rounded-2xl border border-[#d4a574]/20 bg-[#2a2420] p-8 text-center">
                  <div className="mb-4 flex justify-center">
                    <div className="rounded-full bg-[#d4a574]/20 p-4">
                      <svg className="h-8 w-8 text-[#d4a574]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-[#d4a574]">AI Strategy Designer</h3>
                  <p className="text-[#a0826d]">
                    Chat with Prophet AI to create custom trading strategies tailored to your goals
                  </p>
                </div>

                <div className="rounded-2xl border border-[#d4a574]/20 bg-[#2a2420] p-8 text-center">
                  <div className="mb-4 flex justify-center">
                    <div className="rounded-full bg-[#d4a574]/20 p-4">
                      <svg className="h-8 w-8 text-[#d4a574]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-[#d4a574]">Deep Market Analysis</h3>
                  <p className="text-[#a0826d]">
                    Analyze years of historical data with advanced technical indicators
                  </p>
                </div>

                <div className="rounded-2xl border border-[#d4a574]/20 bg-[#2a2420] p-8 text-center">
                  <div className="mb-4 flex justify-center">
                    <div className="rounded-full bg-[#d4a574]/20 p-4">
                      <svg className="h-8 w-8 text-[#d4a574]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="mb-3 text-xl font-bold text-[#d4a574]">Automated Execution</h3>
                  <p className="text-[#a0826d]">
                    Deploy strategies instantly with real-time monitoring and alerts
                  </p>
                </div>
              </div>
            </div>
          </section>
        </main>
        <Footer />
      </div>
    </AdminLoginWall>
  );
}
