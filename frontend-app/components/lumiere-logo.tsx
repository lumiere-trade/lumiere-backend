import Image from "next/image"

export function LumiereLogo() {
  return (
    <div className="flex items-center gap-4">
      <Image src="/images/lumiere-logo.png" alt="Lumiere Logo" width={60} height={60} className="object-contain" />
      <div className="flex flex-col">
        <span className="text-3xl font-bold tracking-wider text-primary">LUMIERE</span>
        <span className="text-[13px] tracking-wide text-muted-foreground/80">
          Blind to emotion, guided by algorithm
        </span>
      </div>
    </div>
  )
}
