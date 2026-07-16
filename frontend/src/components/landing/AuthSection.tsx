import { useState } from 'react'
import { cn } from '../../lib/cn'

const inputCls =
  'w-full rounded-lg border border-primary/15 bg-white px-4 py-3 text-primary placeholder:text-primary/35 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20'

export function AuthSection() {
  const [tab, setTab] = useState<'login' | 'register'>('login')

  return (
    <section id="prijava" className="border-t border-primary/10 bg-surface-1/40 px-4 py-16 md:px-12">
      <div className="mx-auto max-w-md">
        <h2 className="mb-8 text-center font-heading text-3xl font-bold text-balance">
          {tab === 'login' ? 'Dobro došao natrag' : 'Napravi račun'}
        </h2>
        <div className="rounded-xl border border-primary/10 bg-surface p-6 shadow-level-2 md:p-8">
          <div className="mb-6 flex border-b border-primary/10" role="tablist" aria-label="Prijava ili registracija">
            {(['login', 'register'] as const).map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className={cn(
                  '-mb-px flex-1 border-b-2 pb-3 text-sm font-semibold transition-colors',
                  tab === t ? 'border-accent text-primary' : 'border-transparent text-muted hover:text-primary',
                )}
              >
                {t === 'login' ? 'Prijava' : 'Registracija'}
              </button>
            ))}
          </div>

          <form className="flex flex-col gap-4" onSubmit={(e) => e.preventDefault()}>
            {tab === 'register' && (
              <div>
                <label htmlFor="username" className="mb-1.5 block text-sm font-semibold">
                  Korisničko ime
                </label>
                <input id="username" name="username" autoComplete="username" className={inputCls} placeholder="npr. matko" />
              </div>
            )}
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-semibold">
                Email
              </label>
              <input id="email" name="email" type="email" autoComplete="email" className={inputCls} placeholder="ime@primjer.hr" />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-semibold">
                Lozinka
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                className={inputCls}
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              className="mt-2 rounded-lg bg-accent py-3 font-semibold text-white transition-colors hover:bg-accent-dark"
            >
              {tab === 'login' ? 'Prijavi se' : 'Registriraj se'}
            </button>
            {tab === 'login' && (
              <button type="button" className="text-sm text-muted hover:text-primary hover:underline">
                Zaboravljena lozinka?
              </button>
            )}
          </form>
        </div>
      </div>
    </section>
  )
}
