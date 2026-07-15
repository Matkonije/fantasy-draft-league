import { NavBar } from './components/landing/NavBar'
import { Hero } from './components/landing/Hero'
import { HowItWorks } from './components/landing/HowItWorks'
import { Leagues } from './components/landing/Leagues'
import { AppPreview } from './components/landing/AppPreview'
import { WhyFdl } from './components/landing/WhyFdl'
import { Faq } from './components/landing/Faq'
import { AuthSection } from './components/landing/AuthSection'
import { Footer } from './components/landing/Footer'

export default function App() {
  return (
    <div className="flex min-h-dvh flex-col">
      <NavBar />
      <main className="flex-grow">
        <Hero />
        <HowItWorks />
        <Leagues />
        <AppPreview />
        <WhyFdl />
        <Faq />
        <AuthSection />
      </main>
      <Footer />
    </div>
  )
}
