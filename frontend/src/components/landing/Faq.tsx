const faqs = [
  {
    q: 'Kako funkcionira snake draft?',
    a: 'Redoslijed biranja se okreće svake runde: tko bira zadnji u prvoj rundi, bira prvi u drugoj. Prvi draft kreće nasumičnim redoslijedom, a svaki sljedeći obrnutim poretkom tablice — najlošiji bira prvi.',
  },
  {
    q: 'Što ako propustim svoj pick?',
    a: 'Svaki pick ima vremensko ograničenje koje postavlja komesar lige. Ako istekne, automatski dobivaš najboljeg dostupnog igrača po bodovima prošle sezone.',
  },
  {
    q: 'Kako rade zamjene igrača (trade)?',
    a: 'Predložiš zamjenu drugom menadžeru — do 3 igrača po strani. Ako je omjer vrijednosti unutar 1.5x, izvršava se odmah. Ako nije, o zamjeni glasa ostatak lige u roku 48 sati.',
  },
  {
    q: 'Mogu li igrati više liga odjednom?',
    a: 'Da. Svaka fantasy liga je vezana uz jedno natjecanje (Premier League, La Liga...) i ima vlastiti draft, tablicu i raspored — a ti možeš imati ekipu u svakoj.',
  },
]

export function Faq() {
  return (
    <section id="faq" className="mx-auto max-w-3xl px-4 py-16 md:px-12">
      <h2 className="mb-10 text-center font-heading text-3xl font-bold text-balance">Česta pitanja</h2>
      <div className="flex flex-col gap-3">
        {faqs.map((f) => (
          <details
            key={f.q}
            className="group rounded-lg border border-primary/10 bg-surface-1 open:shadow-level-2"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 font-heading text-lg font-bold [&::-webkit-details-marker]:hidden">
              {f.q}
              <span className="ml-4 text-accent transition-transform group-open:rotate-45" aria-hidden="true">
                +
              </span>
            </summary>
            <p className="px-5 pb-5 text-muted text-pretty">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  )
}
