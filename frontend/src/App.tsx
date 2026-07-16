import { NavBar } from './components/landing/NavBar'
import { Hero } from './components/landing/Hero'
import { Leagues } from './components/landing/Leagues'
import { Footer } from './components/landing/Footer'

// sections match the Figma design 1:1; "Kako radi" and login arrive
// once their Figma screens are done
export default function App() {
  return (
    <div className="flex min-h-dvh flex-col">
      <NavBar />
      <main className="flex-grow">
        <Hero />
        <Leagues />
      </main>
      <Footer />
    </div>
  )
}
