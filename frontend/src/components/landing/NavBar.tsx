const links = [
  { href: '#lige', label: 'Lige' },
  { href: '#kako-radi', label: 'Kako radi' },
]

export function NavBar() {
  return (
    <header className="sticky top-3 z-50 px-3 md:px-6">
      {/* full green rounded bar, per Figma */}
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between rounded-2xl bg-accent px-3 shadow-level-2 md:px-5">
        <a href="#" aria-label="FDL — početna" className="flex items-center">
          <img src="/logos/fdl-crest.png" alt="FDL grb" className="h-10 w-auto object-contain" />
        </a>
        <nav className="flex items-center gap-8">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-semibold text-white transition-opacity hover:opacity-80"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <a
          href="#"
          className="rounded-full bg-white px-5 py-1.5 text-sm font-semibold text-accent-dark transition-colors hover:bg-surface"
        >
          Pridruži se
        </a>
      </div>
    </header>
  )
}
