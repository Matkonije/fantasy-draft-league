import { Suspense, useEffect, useMemo, useRef, type MutableRefObject } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { useGLTF } from '@react-three/drei'
import * as THREE from 'three'

// illusion: ball right in front of the camera, goal far away in the distance
const BALL_START = new THREE.Vector3(0, -0.15, 2.3)
const GOAL_POS = new THREE.Vector3(0, -1.2, -14)
// end of flight: INSIDE the goal mouth (below the crossbar, right of centre)
const GOAL_ENTRY = new THREE.Vector3(2.1, 0.25, -13.1)
const CAMERA: [number, number, number] = [0, 0.2, 4.5]
const CAMERA_FAR = 40
const FOV = 42
const TRAVEL_END = 0.84 // scroll progress at which the ball crosses the goal line
const GOAL_BLUR_PX = 9 // starting blur of the distant goal, decays to 0 by 75% scroll

const clamp01 = (v: number) => Math.min(1, Math.max(0, v))
const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2)

/** Scale + center a GLB of unknown size to a target max dimension. */
function useNormalized(url: string, targetSize: number) {
  const { scene } = useGLTF(url)
  return useMemo(() => {
    const cloned = scene.clone(true)
    const box = new THREE.Box3().setFromObject(cloned)
    const size = box.getSize(new THREE.Vector3())
    const scale = targetSize / Math.max(size.x, size.y, size.z)
    const center = box.getCenter(new THREE.Vector3())
    cloned.position.sub(center).multiplyScalar(scale)
    cloned.scale.setScalar(scale)
    const group = new THREE.Group()
    group.add(cloned)
    return group
  }, [scene, targetSize])
}

function SceneLights() {
  return (
    <>
      <ambientLight intensity={0.9} />
      <directionalLight position={[4, 6, 5]} intensity={1.6} />
      <directionalLight position={[-5, 2, -3]} intensity={0.5} />
    </>
  )
}

function Ball({ progressRef }: { progressRef: MutableRefObject<number> }) {
  const model = useNormalized('/models/soccer-ball.glb', 1.4)
  const group = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    const g = group.current
    if (!g) return
    const p = progressRef.current

    // idle spin that speeds up with scroll
    g.rotation.y += delta * (0.35 + p * 4)
    g.rotation.x += delta * (0.15 + p * 1.5)

    // fly from "right in front of the nose" into the goal mouth;
    // perspective shrinks the ball until it matches the goal's scale
    const t = easeInOut(clamp01(p / TRAVEL_END))
    g.position.lerpVectors(BALL_START, GOAL_ENTRY, t)

    // extra frames after crossing the line: the ball pushes into the net,
    // dips slightly and shrinks away instead of popping out instantly
    const into = clamp01((p - TRAVEL_END) / 0.12)
    g.position.z -= into * 1.1
    g.position.y -= into * 0.2
    g.scale.setScalar(Math.max(1 - into, 0.0001))
  })

  return <group ref={group}><primitive object={model} /></group>
}

function Goal({ progressRef, fadeInstead }: { progressRef: MutableRefObject<number>; fadeInstead: boolean }) {
  const model = useNormalized('/models/soccer-goal.glb', 8)
  const materials = useMemo(() => {
    const mats: THREE.Material[] = []
    if (fadeInstead) {
      model.traverse((o) => {
        if (o instanceof THREE.Mesh) {
          const m = o.material as THREE.Material
          m.transparent = true
          mats.push(m)
        }
      })
    }
    return mats
  }, [model, fadeInstead])

  useFrame(() => {
    if (!fadeInstead) return
    // mobile: no blur pipeline — the goal simply fades in as the ball approaches
    const p = clamp01(progressRef.current / TRAVEL_END)
    for (const m of materials) m.opacity = 0.25 + 0.75 * p
  })

  return <primitive object={model} position={GOAL_POS.toArray()} />
}

/**
 * Two stacked transparent canvases with identical cameras:
 *  - back layer: the goal, CSS-blurred; blur decays with scroll (sharp by 75%)
 *  - front layer: the ball, never blurred, always pin-sharp
 */
export function HeroScene({ progressRef }: { progressRef: MutableRefObject<number> }) {
  const isMobile = useMemo(() => window.matchMedia('(max-width: 767px)').matches, [])
  const goalLayerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isMobile) return
    let raf = 0
    let lastBlur = -1
    const tick = () => {
      const p = clamp01(progressRef.current / 0.75)
      const blur = Math.round(GOAL_BLUR_PX * (1 - p) * 10) / 10
      if (blur !== lastBlur && goalLayerRef.current) {
        goalLayerRef.current.style.filter = blur > 0.2 ? `blur(${blur}px)` : 'none'
        lastBlur = blur
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [isMobile, progressRef])

  const canvasProps = {
    style: { width: '100%', height: '100%' } as const,
    dpr: (isMobile ? [1, 1.5] : [1, 2]) as [number, number],
    camera: { position: CAMERA, fov: FOV, far: CAMERA_FAR },
    gl: { antialias: true, alpha: true },
  }

  return (
    <div className="absolute inset-0">
      <div ref={goalLayerRef} className="absolute inset-0" style={isMobile ? undefined : { filter: `blur(${GOAL_BLUR_PX}px)` }}>
        <Canvas {...canvasProps}>
          <SceneLights />
          <Suspense fallback={null}>
            <Goal progressRef={progressRef} fadeInstead={isMobile} />
          </Suspense>
        </Canvas>
      </div>
      <div className="absolute inset-0">
        <Canvas {...canvasProps}>
          <SceneLights />
          <Suspense fallback={null}>
            <Ball progressRef={progressRef} />
          </Suspense>
        </Canvas>
      </div>
    </div>
  )
}

useGLTF.preload('/models/soccer-ball.glb')
useGLTF.preload('/models/soccer-goal.glb')
