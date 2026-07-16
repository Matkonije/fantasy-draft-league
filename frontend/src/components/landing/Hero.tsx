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

          // title reveal ONLY at the "goal" moment — ball reaches the net at ~0.82
          const t = clamp01((p - 0.82) / 0.12)
          gsap.set(titleRef.current, {
            opacity: t,
            y: 48 * (1 - t),
            scale: 0.96 + 0.04 * t,
          })

          // tagline + CTA follow right after the title
          const g = clamp01((p - 0.9) / 0.1)
          gsap.set(taglineRef.current, { opacity: g, y: 24 * (1 - g) })

          // scroll hint fades out immediately; scene dims slightly once the title owns the stage
          gsap.set(scrollHintRef.current, { opacity: 1 - clamp01(p * 6) })
          gsap.set(sceneWrapRef.current, { opacity: 1 - 0.4 * clamp01((p - 0.92) / 0.08) })
        },
      })
    }, wrapRef)
    return () => ctx.revert()
  }, [])

  return (
    <div ref={wrapRef} className="relative h-[300vh]">
      <section className="sticky top-0 h-dvh overflow-hidden text-center">
        {/* full-screen 3D scene, no container — ball and goal live on the page background */}
        <div ref={sceneWrapRef} className="absolute inset-0 z-0">
          <Suspense fallback={null}>
            <HeroScene progressRef={progressRef} />
          </Suspense>
        </div>

        {/* eyebrow */}
        <div className="pointer-events-none absolute inset-x-0 top-24 z-20 mx-auto flex w-full max-w-lg items-center gap-4 px-4 opacity-70 md:top-28">
          <div className="h-px flex-grow bg-primary" />
          <span className="whitespace-nowrap text-xs font-semibold uppercase tracking-[0.2em] md:text-sm">
            Fantasy football, reimagined
          </span>
          <div className="h-px flex-grow bg-primary" />
        </div>

        {/* hero title — hidden until the ball hits the net */}
        <h1
          ref={titleRef}
          className="hero-title pointer-events-none absolute inset-x-0 top-[44%] z-10 -translate-y-1/2 uppercase opacity-0"
        >
          Fantasy
          <br />
          Draft
          <br />
          League
        </h1>

        {/* tagline + CTA — clearly separated from the title, near the bottom */}
        <div
          ref={taglineRef}
          className="absolute inset-x-0 bottom-14 z-20 mx-auto flex max-w-2xl flex-col items-center px-4 opacity-0 md:bottom-20"
        >
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
          className="absolute bottom-6 left-1/2 z-20 flex -translate-x-1/2 flex-col items-center gap-2 opacity-60"
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
