import { Suspense, useMemo, useRef, type MutableRefObject } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { useGLTF } from '@react-three/drei'
import { EffectComposer, DepthOfField } from '@react-three/postprocessing'
import * as THREE from 'three'

const BALL_START = new THREE.Vector3(0, 0, 0)
const GOAL_CORNER = new THREE.Vector3(1.7, 1.45, -5.6) // top-right corner of the goal
const GOAL_POS = new THREE.Vector3(0, -1.7, -7)
const CAMERA_Z = 4.5
const CAMERA_FAR = 30

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

function Ball({ progressRef }: { progressRef: MutableRefObject<number> }) {
  const model = useNormalized('/models/soccer-ball.glb', 1.5)
  const group = useRef<THREE.Group>(null)

  useFrame((_, delta) => {
    const g = group.current
    if (!g) return
    const p = progressRef.current

    // idle spin that speeds up with scroll
    g.rotation.y += delta * (0.35 + p * 4)
    g.rotation.x += delta * (0.15 + p * 1.5)

    // travel toward the top-right corner of the goal over 0-70% scroll
    const t = easeInOut(clamp01(p / 0.7))
    g.position.lerpVectors(BALL_START, GOAL_CORNER, t)

    // the ball "enters the goal" and vanishes right after the reveal starts
    const s = 1 - clamp01((p - 0.8) / 0.1)
    g.scale.setScalar(Math.max(s, 0.0001))
  })

  return <group ref={group}><primitive object={model} /></group>
}

function Goal({ progressRef, fadeInstead }: { progressRef: MutableRefObject<number>; fadeInstead: boolean }) {
  const model = useNormalized('/models/soccer-goal.glb', 6)
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
    // mobile: no depth-of-field — the goal simply fades in as focus "shifts" to it
    const p = clamp01(progressRef.current / 0.7)
    for (const m of materials) m.opacity = 0.3 + 0.7 * p
  })

  return <primitive object={model} position={GOAL_POS.toArray()} />
}

function FocusRig({ progressRef, dofRef }: { progressRef: MutableRefObject<number>; dofRef: MutableRefObject<any> }) {
  useFrame(() => {
    const effect = dofRef.current
    if (!effect) return
    const p = clamp01(progressRef.current / 0.7)
    // focus moves from the ball plane to the goal plane (normalized by camera far)
    const ballDist = CAMERA_Z / CAMERA_FAR
    const goalDist = (CAMERA_Z + Math.abs(GOAL_POS.z)) / CAMERA_FAR
    const uniforms = effect.cocMaterial?.uniforms
    if (uniforms?.focusDistance) uniforms.focusDistance.value = THREE.MathUtils.lerp(ballDist, goalDist, p)
  })
  return null
}

export function HeroScene({ progressRef }: { progressRef: MutableRefObject<number> }) {
  const isMobile = useMemo(() => window.matchMedia('(max-width: 767px)').matches, [])
  const dofRef = useRef<any>(null)

  return (
    <Canvas
      style={{ width: '100%', height: '100%' }}
      dpr={isMobile ? [1, 1.5] : [1, 2]}
      camera={{ position: [0, 0.2, CAMERA_Z], fov: 42, far: CAMERA_FAR }}
      gl={{ antialias: true, alpha: true }}
    >
      <ambientLight intensity={0.9} />
      <directionalLight position={[4, 6, 5]} intensity={1.6} />
      <directionalLight position={[-5, 2, -3]} intensity={0.5} />
      <Suspense fallback={null}>
        <Ball progressRef={progressRef} />
        <Goal progressRef={progressRef} fadeInstead={isMobile} />
        {!isMobile && (
          <EffectComposer>
            <DepthOfField ref={dofRef} focusDistance={CAMERA_Z / CAMERA_FAR} focalLength={0.04} bokehScale={5} />
          </EffectComposer>
        )}
        {!isMobile && <FocusRig progressRef={progressRef} dofRef={dofRef} />}
      </Suspense>
    </Canvas>
  )
}

useGLTF.preload('/models/soccer-ball.glb')
useGLTF.preload('/models/soccer-goal.glb')
