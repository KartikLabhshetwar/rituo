"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Navigation } from "@/components/landing/navigation"
import { HeroSection } from "@/components/landing/hero-section"
import { FeaturesSection } from "@/components/landing/features-section"
import { BenefitsSection } from "@/components/landing/benefits-section"
import { StatsSection } from "@/components/landing/stats-section"
import { CTASection } from "@/components/landing/cta-section"
import { Footer } from "@/components/landing/footer"

export default function LandingPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('access_token')
    const apiKey = localStorage.getItem('groq_api_key')
    
    if (token && apiKey) {
      // User is fully set up, redirect to chat
      router.push('/chat')
      return
    }
    
    if (token) {
      // User is authenticated but needs API key
      setIsAuthenticated(true)
    }
    
    setIsLoading(false)
  }, [router])

    const handleGetStarted = () => {
    if (isAuthenticated) {
      // User is authenticated, go to API key setup
      router.push('/chat')
    } else {
      // User needs to authenticate first
      router.push('/login')
    }
  }

  const handleSignIn = () => {
    router.push('/login')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation 
        isAuthenticated={isAuthenticated}
        onSignIn={handleSignIn}
        onGetStarted={handleGetStarted}
      />
      
      <HeroSection 
        isAuthenticated={isAuthenticated}
        onGetStarted={handleGetStarted}
      />
      
      <FeaturesSection />
      
      <BenefitsSection />
      
      <StatsSection />
      
      <CTASection 
        isAuthenticated={isAuthenticated}
        onGetStarted={handleGetStarted}
      />
      
      <Footer />
    </div>
  )
}