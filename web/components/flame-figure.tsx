// The product's idea in one picture: NASA tested fire at 0 g (round blue flame) and at 1 g
// (teardrop flame), but never at lunar gravity (dashed, empty).
export function FlameFigure({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 300 150"
      role="img"
      aria-label="Flames NASA tested at 0 g and 1 g, and the untested Moon case"
      className={className}
    >
      <defs>
        <radialGradient id="zero-g-flame" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="35%" stopColor="#9db4ff" />
          <stop offset="75%" stopColor="var(--zero-g)" />
          <stop offset="100%" stopColor="var(--zero-g)" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="one-g-flame" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#3d5bd9" />
          <stop offset="25%" stopColor="#f5c46b" />
          <stop offset="100%" stopColor="var(--one-g)" />
        </linearGradient>
      </defs>

      <circle cx="50" cy="62" r="34" fill="url(#zero-g-flame)" />
      <path d="M150 20 C 168 50, 178 70, 170 88 A 22 22 0 0 1 130 88 C 122 70, 132 50, 150 20 Z" fill="url(#one-g-flame)" />
      <circle cx="250" cy="62" r="30" fill="none" stroke="var(--gap)" strokeWidth="2" strokeDasharray="6 6" />

      <g fontFamily="inherit" fontSize="13" textAnchor="middle" fill="var(--ink)">
        <text x="50" y="122" fontWeight="700">0 g</text>
        <text x="150" y="122" fontWeight="700">1 g</text>
        <text x="250" y="122" fontWeight="700">Moon</text>
      </g>
      <g fontFamily="inherit" fontSize="11" textAnchor="middle" fill="var(--gap)">
        <text x="50" y="139">tested in orbit</text>
        <text x="150" y="139">tested on Earth</text>
        <text x="250" y="139">never tested</text>
      </g>
    </svg>
  );
}
