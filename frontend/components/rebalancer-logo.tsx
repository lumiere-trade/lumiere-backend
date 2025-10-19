export function RebalancerLogo() {
  return (
    <div className="flex items-center gap-3">
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-primary"
      >
        <path
          d="M24 4L20 12H16L12 20V28L16 36H20L24 44L28 36H32L36 28V20L32 12H28L24 4Z"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="24" cy="16" r="3" fill="currentColor" />
        <path d="M24 20V32M20 28L24 32L28 28" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <span className="text-2xl font-bold tracking-wider text-primary">REBALANCER</span>
    </div>
  )
}
