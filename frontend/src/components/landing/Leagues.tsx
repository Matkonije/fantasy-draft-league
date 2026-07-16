import { cn } from '../../lib/cn'

type Band = {
  name: string
  logo: string
  logoClass?: string // e.g. invert to white on dark brand backgrounds
  text: string
  bg: string
  fg: string
  logoRight?: boolean
}

const bands: Band[] = [
  {
    name: 'Premier League',
    logo: '/logos/premier-league.svg',
    logoClass: 'brightness-0 invert', // purple logo -> white on the purple band
    text: 'Engleska elita: 20 klubova, 38 kola, službeni FPL podaci.',
    bg: 'bg-[#3D195B]',
    fg: 'text-white',
  },
  {
    name: 'LALIGA',
    logo: '/logos/laliga.png',
    text: 'Španjolski prvoligaški nogomet, od Madrida do Barcelone.',
    bg: 'bg-[#0E0E0E]',
    fg: 'text-[#FF4B44]',
    logoRight: true,
  },
  {
    name: 'Ligue 1',
    logo: '/logos/ligue1.svg',
    text: 'Francuska liga i njezine buduće superzvijezde.',
    bg: 'bg-white',
    fg: 'text-[#101010]',
  },
  {
    name: 'Bundesliga',
    logo: '/logos/bundesliga.svg',
    logoClass: 'brightness-0 invert', // red logo -> white on the red band
    text: 'Njemačka liga: najviše golova po kolu u Europi.',
    bg: 'bg-[#D20515]',
    fg: 'text-white',
    logoRight: true,
  },
  {
    name: 'Serie A',
    logo: '/logos/serie-a.svg',
    text: 'Talijanska taktička škola nogometa.',
    bg: 'bg-white',
    fg: 'text-[#024494]',
  },
]

export function Leagues() {
  return (
    <section id="lige" aria-label="Podržana natjecanja">
      {bands.map((b) => (
        <div key={b.name} className={cn(b.bg, b.fg)}>
          <div
            className={cn(
              'mx-auto flex min-h-48 max-w-5xl flex-col items-center justify-between gap-6 px-6 py-10 md:flex-row md:gap-16 md:px-10',
              b.logoRight && 'md:flex-row-reverse',
            )}
          >
            <img
              src={b.logo}
              alt={b.name}
              className={cn('h-24 w-auto max-w-64 object-contain md:h-32', b.logoClass)}
            />
            <p className="max-w-md text-center text-sm opacity-90 md:text-left md:text-base text-pretty">
              {b.text}
            </p>
          </div>
        </div>
      ))}
    </section>
  )
}
