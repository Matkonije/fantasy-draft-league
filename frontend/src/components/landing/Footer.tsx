const links = ['O nama', 'Pravila', 'Kontakt', 'Privatnost']

export function Footer() {
  return (
    <footer className="mt-auto border-t border-primary/10 bg-surface-2">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-6 px-4 py-10 md:flex-row md:px-12">
        <div className="font-heading text-xl font-bold">FDL</div>
        <nav className="flex flex-wrap justify-center gap-6">
          {links.map((l) => (
            <a
              key={l}
              href="#"
              className="rounded text-xs font-medium text-muted transition-colors hover:text-primary hover:underline focus:outline-none focus:ring-2 focus:ring-accent"
            >
              {l}
            </a>
          ))}
        </nav>
        <div className="text-xs text-muted">© 2026 Fantasy Draft League. Sva prava pridržana.</div>
      </div>
      <div className="border-t border-primary/5 px-4 py-3 text-center text-[11px] text-muted/70">
        3D model "Soccer Ball" by tinmanjuggernaut, licensed under CC Attribution.
      </div>
    </footer>
  )
}
