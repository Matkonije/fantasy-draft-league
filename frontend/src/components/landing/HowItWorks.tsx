const steps = [
  {
    title: 'Draft',
    text: 'Okupi prijatelje i odradite uživo snake draft. Svaki igrač može biti samo u jednoj ekipi.',
    icon: (
      <svg viewBox="0 0 24 24" className="size-9" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <circle cx="9" cy="8" r="3" />
        <circle cx="17" cy="10" r="2.5" />
        <path d="M3.5 19c.5-3 2.8-4.5 5.5-4.5s5 1.5 5.5 4.5M14.5 19c.3-2 1.4-3.2 3-3.6 1.7-.4 3.4.6 3.9 2.6" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: 'Sastavi tim',
    text: 'Svako kolo prilagodi formaciju i prvih 11 temeljem stvarnih nastupa igrača.',
    icon: (
      <svg viewBox="0 0 24 24" className="size-9" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <path d="M8 6h12M8 12h12M8 18h12" strokeLinecap="round" />
        <path d="M4 5v2M3.2 6h1.6M4 11.2v1.6M3.2 12.8h1.6M4 17v2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: 'Prati bodove',
    text: 'Bodovi se ažuriraju uživo tijekom utakmica. Detaljna statistika za svaku akciju.',
    icon: (
      <svg viewBox="0 0 24 24" className="size-9" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <path d="M4 20V10M10 20V4M16 20v-8M21 20H3" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: 'Trade s ligom',
    text: 'Pregovaraj i mijenjaj igrače s drugim menadžerima u ligi kako bi pojačao kritične pozicije.',
    icon: (
      <svg viewBox="0 0 24 24" className="size-9" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <path d="M4 8h14l-3-3M20 16H6l3 3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
]

export function HowItWorks() {
  return (
    <section id="kako-radi" className="mx-auto max-w-7xl border-t border-primary/10 px-4 py-16 md:px-12">
      <h2 className="mb-12 text-center font-heading text-3xl font-bold text-balance">Kako radi</h2>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {steps.map((s) => (
          <div
            key={s.title}
            className="group rounded-lg border border-primary/10 bg-surface-1 p-6 transition-shadow hover:shadow-level-2"
          >
            <div className="mb-4 text-primary transition-colors group-hover:text-accent">{s.icon}</div>
            <h3 className="mb-2 font-heading text-xl font-bold">{s.title}</h3>
            <p className="text-muted text-pretty">{s.text}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
