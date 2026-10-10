/** The cartoon stethoscope: binaurals bent into a heart with a pulse line in
 * it, tubing draped over a ℞ pad that carries the approval stamp - the
 * product's promise drawn as one picture. Colours come from the doodle
 * tokens in globals.css, so the drawing follows light and dark mode. */

const LINE = "var(--color-doodle-line)";
const STEEL = "var(--color-doodle-steel)";
const GLINT = "var(--color-doodle-glint)";
const SPARK = "var(--color-doodle-spark)";

const BINAURAL_L = "M268 120C246 58 140 52 132 146c-6 74 92 128 168 196";
const BINAURAL_R = "M332 120C354 58 460 52 468 146c6 74-92 128-168 196";
const TUBE = "M300 352C300 420 362 424 362 492C362 568 280 576 223 593";

export function StethoscopeArt({
  variant = "scene",
  className,
}: {
  /** "scene" adds the backdrop, the ℞ pad and sparkles; "mark" is the
   * instrument alone, for small spots such as empty states. */
  variant?: "scene" | "mark";
  className?: string;
}) {
  const scene = variant === "scene";
  return (
    <svg
      viewBox={scene ? "0 0 620 720" : "40 40 460 650"}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {scene && (
        <>
          <path
            d="M300 40c120-10 250 40 270 170s-30 200 10 300-90 190-230 180S70 650 40 520 10 330 60 220 180 50 300 40Z"
            fill="var(--color-doodle-sky)"
          />

          {/* ℞ pad with the physician's stamp */}
          <g transform="translate(4 0) rotate(7 450 530)">
            <rect x="330" y="370" width="240" height="300" rx="22" fill="var(--color-doodle-paper)" stroke={LINE} strokeWidth="6" />
            <rect x="410" y="352" width="80" height="34" rx="12" fill={STEEL} stroke={LINE} strokeWidth="6" />
            <path d="M404 418v58m0-58h22a16 16 0 0 1 0 32h-22m14 0 30 30m-24 4 20-20" stroke="var(--color-doodle-ink)" strokeWidth="7" />
            <path d="M370 512h150M370 546h170M370 580h120" stroke="var(--color-doodle-rule)" strokeWidth="9" />
            <g transform="rotate(-12 500 620)" stroke="var(--color-doodle-ink)">
              <circle cx="500" cy="622" r="34" strokeWidth="5" />
              <circle cx="500" cy="622" r="26" strokeWidth="2.5" />
              <path d="m486 623 10 10 19-21" strokeWidth="6" />
            </g>
          </g>
        </>
      )}

      {/* heart and pulse, inside the binaurals */}
      <g className={scene ? "heart-beat" : undefined}>
        <path
          d="M300 150C282 92 168 70 158 150c-7 62 74 118 142 175 68-57 149-113 142-175-10-80-124-58-142 0Z"
          fill="var(--color-doodle-heart)"
        />
        <path d="M196 214h52l14-30 20 62 16-46 12 14h86" stroke={GLINT} strokeWidth="7" />
      </g>

      {/* binaurals: outline, metal, glint */}
      <path d={BINAURAL_L} stroke={LINE} strokeWidth="22" />
      <path d={BINAURAL_R} stroke={LINE} strokeWidth="22" />
      <path d={BINAURAL_L} stroke={STEEL} strokeWidth="10" />
      <path d={BINAURAL_R} stroke={STEEL} strokeWidth="10" />
      <path d="M200 84c-30 8-48 30-52 60M400 84c30 8 48 30 52 60" stroke={GLINT} strokeWidth="3.5" />

      {/* ear tips */}
      <ellipse cx="274" cy="134" rx="15" ry="21" transform="rotate(-20 274 134)" fill="var(--color-doodle-tip)" stroke={LINE} strokeWidth="6" />
      <ellipse cx="326" cy="134" rx="15" ry="21" transform="rotate(20 326 134)" fill="var(--color-doodle-tip)" stroke={LINE} strokeWidth="6" />
      <path d="M269 124c-2 4-2 9 0 13M331 124c2 4 2 9 0 13" stroke={GLINT} strokeWidth="3.5" />

      {/* tubing */}
      <path d={TUBE} stroke={LINE} strokeWidth="34" />
      <path d={TUBE} stroke="var(--color-doodle-tube)" strokeWidth="20" />
      <path d="M308 384c8 26 42 34 48 70" stroke="var(--color-doodle-tube-hi)" strokeWidth="5" />
      <rect x="284" y="322" width="32" height="44" rx="12" fill={STEEL} stroke={LINE} strokeWidth="6" />

      {/* chest piece */}
      <g transform="translate(140 615) rotate(75)">
        <rect x="-16" y="-92" width="32" height="46" rx="10" fill={STEEL} stroke={LINE} strokeWidth="6" />
        <circle r="62" fill="var(--color-doodle-steel-shade)" stroke={LINE} strokeWidth="7" />
        <circle cx="5" r="51" fill={STEEL} stroke={LINE} strokeWidth="4" />
        <circle cx="5" r="33" fill={GLINT} fillOpacity=".55" />
        <path d="M-20 -28c-12 8-18 22-18 36" stroke={GLINT} strokeWidth="5" />
      </g>

      {scene && (
        <>
          {/* listening marks and sparkles */}
          <path d="M70 690c-12-6-20-16-24-28M52 708c-20-10-32-26-38-46" stroke={SPARK} strokeWidth="5" />
          <path d="M520 70l6 18 18 6-18 6-6 18-6-18-18-6 18-6Z" fill="var(--color-doodle-tip)" stroke={SPARK} strokeWidth="4" />
          <path d="M90 270l4 12 12 4-12 4-4 12-4-12-12-4 12-4Z" fill={GLINT} stroke={SPARK} strokeWidth="4" />
          <path d="M60 120v20M50 130h20M555 300v16M547 308h16" stroke={SPARK} strokeWidth="4" />
          <circle cx="470" cy="300" r="6" fill="var(--color-doodle-tip)" stroke={SPARK} strokeWidth="3" />
        </>
      )}
    </svg>
  );
}
