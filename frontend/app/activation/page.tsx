"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { NavigationHeader } from "@/components/navigation-header"
import { CheckCircle2, Lock, Wallet, Zap, Shield } from "lucide-react"

export default function ActivationPage() {
  const [selectedPlan, setSelectedPlan] = useState<"basic" | "pro" | "elite">("pro")
  const [depositAmount, setDepositAmount] = useState("1000")
  const [step, setStep] = useState<"subscription" | "deposit" | "confirm">("subscription")

  const plans = [
    {
      id: "basic" as const,
      name: "Basic",
      price: "49",
      features: ["1 Active Strategy", "Daily Rebalancing", "Email Notifications", "Basic Analytics"],
    },
    {
      id: "pro" as const,
      name: "Pro",
      price: "149",
      features: [
        "5 Active Strategies",
        "Hourly Rebalancing",
        "Real-time Notifications",
        "Advanced Analytics",
        "Priority Support",
      ],
      popular: true,
    },
    {
      id: "elite" as const,
      name: "Elite",
      price: "499",
      features: [
        "Unlimited Strategies",
        "Minute-level Rebalancing",
        "Multi-channel Alerts",
        "Custom Indicators",
        "Dedicated Support",
        "API Access",
      ],
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <NavigationHeader currentPage="forger" />

      <div className="container mx-auto px-6 pt-24">
        <div className="mb-8 text-center">
          <h1 className="mb-4 text-6xl font-bold tracking-tight text-primary">ACTIVATE STRATEGY</h1>
          <p className="text-xl text-muted-foreground">Choose your plan and deposit funds to begin live trading</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12 flex justify-center gap-4">
          {[
            { id: "subscription", label: "Subscription" },
            { id: "deposit", label: "Deposit Funds" },
            { id: "confirm", label: "Confirm" },
          ].map((s, index) => (
            <div key={s.id} className="flex items-center gap-4">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-full border-2 ${
                    step === s.id ? "border-primary bg-primary/20" : "border-muted-foreground/30"
                  }`}
                >
                  <span className="font-bold">{index + 1}</span>
                </div>
                <span className="text-sm font-medium">{s.label}</span>
              </div>
              {index < 2 && <div className="h-0.5 w-16 bg-muted-foreground/30" />}
            </div>
          ))}
        </div>

        {/* Subscription Step */}
        {step === "subscription" && (
          <div className="mx-auto max-w-6xl">
            <div className="mb-8 grid gap-6 md:grid-cols-3">
              {plans.map((plan) => (
                <Card
                  key={plan.id}
                  className={`relative cursor-pointer border-2 p-6 transition-all hover:border-primary/50 ${
                    selectedPlan === plan.id ? "border-primary bg-primary/5" : "border-border"
                  }`}
                  onClick={() => setSelectedPlan(plan.id)}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="rounded-full bg-primary px-4 py-1 text-xs font-bold text-primary-foreground">
                        POPULAR
                      </span>
                    </div>
                  )}

                  <div className="mb-6 text-center">
                    <h3 className="mb-2 text-2xl font-bold">{plan.name}</h3>
                    <div className="flex items-baseline justify-center gap-1">
                      <span className="text-4xl font-bold text-primary">${plan.price}</span>
                      <span className="text-muted-foreground">/month</span>
                    </div>
                  </div>

                  <ul className="space-y-3">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2">
                        <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ))}
            </div>

            <div className="flex justify-center">
              <Button
                size="lg"
                className="rounded-full px-12 py-6 text-lg font-bold"
                onClick={() => setStep("deposit")}
              >
                CONTINUE TO DEPOSIT
              </Button>
            </div>
          </div>
        )}

        {/* Deposit Step */}
        {step === "deposit" && (
          <div className="mx-auto max-w-2xl">
            <Card className="border-primary/20 p-8">
              <div className="mb-6 flex items-center gap-3">
                <Wallet className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">Deposit Trading Funds</h2>
              </div>

              <div className="mb-6 rounded-lg bg-muted/50 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="h-4 w-4" />
                  <span>Funds are locked in a secure smart contract during trading</span>
                </div>
              </div>

              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium">Deposit Amount (USDT)</label>
                <Input
                  type="number"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="text-lg"
                  placeholder="1000"
                />
                <div className="mt-2 flex gap-2">
                  {["500", "1000", "5000", "10000"].map((amount) => (
                    <Button
                      key={amount}
                      variant="outline"
                      size="sm"
                      className="rounded-full bg-transparent"
                      onClick={() => setDepositAmount(amount)}
                    >
                      ${amount}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="mb-6 space-y-3 rounded-lg border border-border p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subscription (Pro)</span>
                  <span className="font-medium">$149/month</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Trading Deposit</span>
                  <span className="font-medium">${depositAmount} USDT</span>
                </div>
                <div className="border-t border-border pt-3">
                  <div className="flex justify-between">
                    <span className="font-semibold">Total to Lock</span>
                    <span className="text-lg font-bold text-primary">${depositAmount} USDT</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  size="lg"
                  className="flex-1 rounded-full bg-transparent"
                  onClick={() => setStep("subscription")}
                >
                  BACK
                </Button>
                <Button size="lg" className="flex-1 rounded-full font-bold" onClick={() => setStep("confirm")}>
                  <Lock className="mr-2 h-5 w-5" />
                  LOCK FUNDS
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Confirm Step */}
        {step === "confirm" && (
          <div className="mx-auto max-w-2xl">
            <Card className="border-primary/20 p-8 text-center">
              <div className="mb-6 flex justify-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/20">
                  <Zap className="h-10 w-10 text-primary" />
                </div>
              </div>

              <h2 className="mb-4 text-3xl font-bold">Strategy Deployment in Progress</h2>
              <p className="mb-8 text-lg text-muted-foreground">
                Your dedicated Kubernetes pod is being created with Chevalier, Chronicler, and Courier services
              </p>

              <div className="mb-8 space-y-4">
                {[
                  { name: "Creating Kubernetes Pod", done: true },
                  { name: "Deploying Chevalier (Trade Executor)", done: true },
                  { name: "Initializing Chronicler (Data Feed)", done: true },
                  { name: "Setting up Courier (Notifications)", done: false },
                  { name: "Connecting to Smart Contract", done: false },
                ].map((task) => (
                  <div key={task.name} className="flex items-center justify-between rounded-lg bg-muted/50 p-4">
                    <span>{task.name}</span>
                    {task.done ? (
                      <CheckCircle2 className="h-5 w-5 text-primary" />
                    ) : (
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    )}
                  </div>
                ))}
              </div>

              <Button size="lg" className="rounded-full px-12 py-6 text-lg font-bold" disabled>
                DEPLOYING...
              </Button>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
