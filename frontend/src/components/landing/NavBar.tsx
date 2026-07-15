const links = [
  { href: '#lige', label: 'Lige' },
  { href: '#kako-radi', label: 'Kako radi' },
  { href: '#faq', label: 'FAQ' },
  { href: '#pravila', label: 'Pravila' },
]

export function NavBar() {
  return (
    <header className="sticky top-0 z-50 border-b border-primary/10 bg-surface">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-4 md:px-12">
        <a href="#" className="font-heading text-2xl font-bold" aria-label="FDL — početna">
          FDL
        </a>
        <nav className="hidden gap-2 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="rounded-md px-3 py-2 text-sm font-semibold text-muted transition-colors hover:bg-surface-1 hover:text-primary"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <a
          href="#prijava"
          className="rounded bg-accent px-6 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-hover"
        >
          Započni
        </a>
      </div>
    </header>
  )
}
