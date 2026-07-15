import { lazy, Suspense, useLayoutEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

// three.js is heavy — load the scene as its own chunk so the page shell paints fast
const HeroScene = lazy(() =>
  import('../three/HeroScene').then((m) => ({ default: m.HeroScene })),
)

gsap.registerPlugin(ScrollTrigger)

const clamp01 = (v: number) => Math.min(1, Math.max(0, v))

export function Hero() {
  const wrapRef = useRef<HTMLDivElement>(null)
  const titleRef = useRef<HTMLHeadingElement>(null)
  const taglineRef = useRef<HTMLDivElement>(null)
  const scrollHintRef = useRef<HTMLDivElement>(null)
  const sceneWrapRef = useRef<HTMLDivElement>(null)
  // shared scroll progress, read by the 3D scene every frame
  const progressRef = useRef(0)

  useLayoutEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) {
      // no scroll choreography: title and tagline are simply visible
      gsap.set([titleRef.current, taglineRef.current], { opacity: 1, y: 0, scale: 1 })
      progressRef.current = 1
      return
    }

    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: wrapRef.current,
        start: 'top top',
        end: 'bottom bottom',
        scrub: 0.4,
        onUpdate: (self) => {
          const p = self.progress
          progressRef.current = p

          // title reveal: the "goal" moment at ~72-85% scroll
          const t = clamp01((p - 0.72) / 0.13)
          gsap.set(titleRef.current, {
            opacity: t,
            y: 48 * (1 - t),
            scale: 0.96 + 0.04 * t,
          })

          // tagline + CTA follow right after the title
          const g = clamp01((p - 0.82) / 0.13)
          gsap.set(taglineRef.current, { opacity: g, y: 24 * (1 - g) })

          // scroll hint fades out immediately; 3D scene dims once the title owns the stage
          gsap.set(scrollHintRef.current, { opacity: 1 - clamp01(p * 6) })
          gsap.set(sceneWrapRef.current, { opacity: 1 - 0.55 * clamp01((p - 0.85) / 0.15) })
        },
      })
    }, wrapRef)
    return () => ctx.revert()
  }, [])

  return (
    <div ref={wrapRef} className="relative h-[300vh]">
      <section className="sticky top-0 flex h-dvh flex-col items-center justify-center overflow-hidden px-4 text-center">
        {/* eyebrow */}
        <div className="z-20 mb-6 flex w-full max-w-lg items-center gap-4 opacity-70">
          <div className="h-px flex-grow bg-primary" />
          <span className="whitespace-nowrap text-xs font-semibold uppercase tracking-[0.2em] md:text-sm">
            Fantasy football, reimagined
          </span>
          <div className="h-px flex-grow bg-primary" />
        </div>

        {/* 3D scene frame */}
        <div
          ref={sceneWrapRef}
          className="relative z-0 h-[min(58vh,560px)] w-[min(88vw,860px)] overflow-hidden rounded-xl border border-primary/10 bg-surface-1 shadow-2xl"
        >
          <Suspense fallback={null}>
            <HeroScene progressRef={progressRef} />
          </Suspense>
        </div>

        {/* hero title — hidden until the ball hits the net */}
        <h1
          ref={titleRef}
          className="hero-title pointer-events-none absolute inset-x-0 top-1/2 z-10 -translate-y-1/2 uppercase opacity-0"
        >
          Fantasy
          <br />
          Draft
          <br />
          League
        </h1>

        {/* tagline + CTA */}
        <div ref={taglineRef} className="z-20 mt-8 flex max-w-2xl flex-col items-center opacity-0">
          <p className="mb-6 text-lg font-medium text-muted text-pretty">
            Iskusi pravi nogometni menadžment kroz snake draft sustav gdje je svaki igrač jedinstven
            unutar tvoje lige. Nema duplikata, samo taktika.
          </p>
          <a
            href="#prijava"
            className="rounded-lg bg-accent px-8 py-4 text-lg font-semibold text-white shadow-level-2 transition-transform hover:-translate-y-1 hover:bg-accent-hover"
          >
            Započni svoju ligu
          </a>
        </div>

        {/* scroll hint */}
        <div
          ref={scrollHintRef}
          className="absolute bottom-8 left-1/2 z-20 flex -translate-x-1/2 flex-col items-center gap-2 opacity-60"
        >
          <span className="text-xs font-semibold uppercase tracking-widest">Scroll za više</span>
          <svg viewBox="0 0 24 24" className="size-5 animate-bounce" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M12 4v16m0 0l-6-6m6 6l6-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </section>
    </div>
  )
}
