import { cn } from '../../lib/cn'

type Band = {
  name: string
  text: string
  bg: string
  fg: string
  accent?: string
  logoRight?: boolean
}

// full-width brand bands per league (Figma direction); wordmarks are text
// placeholders until official logo assets land in public/leagues/
const bands: Band[] = [
  {
    name: 'Premier League',
    text: 'Najjača liga svijeta, kompletni podaci uživo kroz službeni FPL sustav bodovanja.',
    bg: 'bg-[#3D195B]',
    fg: 'text-white',
    accent: 'text-[#00FF85]',
  },
  {
    name: 'LALIGA',
    text: 'Tehnička perfekcija juga Europe. El Clásico u tvojoj fantasy ligi.',
    bg: 'bg-[#101010]',
    fg: 'text-white',
    accent: 'text-[#FF4B44]',
    logoRight: true,
  },
  {
    name: 'LIGUE 1',
    text: 'Mladi talenti i parižki sjaj — liga iz koje izlaze sljedeće superzvijezde.',
    bg: 'bg-white',
    fg: 'text-[#101010]',
    accent: 'text-[#091C3E]',
  },
  {
    name: 'Bundesliga',
    text: 'Golovi, pune tribine i visoki presing. Najviše pogodaka po kolu u Europi.',
    bg: 'bg-[#D20515]',
    fg: 'text-white',
    logoRight: true,
  },
  {
    name: 'Serie A',
    text: 'Taktička škola nogometa. Catenaccio protiv tvog napadačkog tria.',
    bg: 'bg-white',
    fg: 'text-[#024494]',
  },
]

export function Leagues() {
  return (
    <section id="lige" aria-label="Podržana natjecanja">
      {bands.map((b) => (
        <div key={b.name} className={cn('border-t border-primary/10', b.bg, b.fg)}>
          <div
            className={cn(
              'mx-auto flex min-h-44 max-w-6xl flex-col items-center justify-between gap-6 px-6 py-10 md:flex-row md:gap-16 md:px-12',
              b.logoRight && 'md:flex-row-reverse',
            )}
          >
            <div className={cn('font-heading text-4xl font-extrabold tracking-tight md:text-5xl', b.accent)}>
              {b.name}
            </div>
            <p className="max-w-md text-center text-sm opacity-85 md:text-left md:text-base text-pretty">
              {b.text}
            </p>
          </div>
        </div>
      ))}
    </section>
  )
}
