export function Footer() {
  return (
    <footer className="mt-auto">
      {/* grass stripes from the Figma design */}
      <div className="h-4 bg-[#7CBF6A]" />
      <div className="h-5 bg-accent" />
      <div className="h-6 bg-[#5E9A4F]" />
      <div className="bg-accent-dark px-4 py-8 text-white">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-4 md:flex-row md:justify-between">
          <img src="/logos/fdl-crest.png" alt="FDL — Fantasy Draft League" className="h-14 w-auto object-contain" />
          <div className="text-center text-xs opacity-85 md:text-right">
            <div>© 2026 Fantasy Draft League. Sva prava pridržana.</div>
            <div className="mt-1">3D model "Soccer Ball" by tinmanjuggernaut, licensed under CC Attribution.</div>
          </div>
        </div>
      </div>
    </footer>
  )
}
