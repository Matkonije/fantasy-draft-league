const rows = [
  { klasik: 'Svi mogu imati Haalanda', fdl: 'Svaki igrač pripada točno jednoj ekipi u ligi' },
  { klasik: 'Tim slažeš sam, protiv algoritma', fdl: 'Tim gradiš uživo na draftu, protiv prijatelja' },
  { klasik: 'Transferi bez posljedica', fdl: 'Trade s fer-provjerom — nepošteni idu na glasanje lige' },
  { klasik: 'Ista taktika cijelu sezonu', fdl: 'Svakih par tjedana novi draft i nova šansa za zadnje' },
]

export function WhyFdl() {
  return (
    <section id="pravila" className="border-t border-primary/10 bg-surface-1/40 px-4 py-16 md:px-12">
      <div className="mx-auto max-w-4xl">
        <h2 className="mb-4 text-center font-heading text-3xl font-bold text-balance">Zašto FDL</h2>
        <p className="mx-auto mb-10 max-w-xl text-center text-muted text-pretty">
          Klasični fantasy igraš protiv tablice. Draft fantasy igraš protiv ljudi koje poznaješ.
        </p>
        <div className="overflow-hidden rounded-lg border border-primary/10 bg-surface">
          <div className="grid grid-cols-2 border-b border-primary/10 bg-surface-1 text-sm font-semibold uppercase tracking-wider">
            <div className="px-5 py-3 text-primary/50">Klasični fantasy</div>
            <div className="px-5 py-3 text-accent">FDL</div>
          </div>
          {rows.map((r) => (
            <div key={r.fdl} className="grid grid-cols-2 border-b border-primary/10 last:border-b-0">
              <div className="px-5 py-4 text-muted">{r.klasik}</div>
              <div className="px-5 py-4 font-medium">{r.fdl}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
