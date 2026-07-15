export function AppPreview() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 md:px-12">
      <h2 className="mb-4 text-center font-heading text-3xl font-bold text-balance">Pogled u aplikaciju</h2>
      <p className="mx-auto mb-10 max-w-xl text-center text-muted text-pretty">
        Draft soba, postava na terenu i tablica lige — sve uživo, sinkronizirano s pravim utakmicama.
      </p>
      {/* Screenshot placeholder — real capture goes here later */}
      <div className="mx-auto flex aspect-video max-w-4xl items-center justify-center rounded-xl border border-primary/10 bg-surface-1 shadow-level-2">
        <span className="text-sm font-semibold uppercase tracking-widest text-primary/40">
          Prikaz sučelja — uskoro
        </span>
      </div>
    </section>
  )
}
