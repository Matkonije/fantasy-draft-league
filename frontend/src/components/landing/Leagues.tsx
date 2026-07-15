const leagues = ['Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1']

export function Leagues() {
  return (
    <section id="lige" className="border-y border-primary/10 bg-surface-1/40 px-4 py-10 md:px-12">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-8 md:flex-row">
        <span className="text-sm font-semibold uppercase tracking-widest text-primary/70">
          Podržana natjecanja
        </span>
        <div className="flex flex-wrap justify-center gap-8 opacity-80 md:gap-12">
          {leagues.map((l) => (
            <span key={l} className="font-heading text-xl font-bold">
              {l}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
