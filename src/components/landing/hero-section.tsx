"use client"

import { SwissContainer, SwissSection, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { SwissButton } from "@/components/ui/swiss-button"
import { ArrowRight } from "lucide-react"

interface HeroSectionProps {
  isAuthenticated: boolean
  onGetStarted: () => void
}

export function HeroSection({ isAuthenticated, onGetStarted }: HeroSectionProps) {
  return (
    <SwissSection className="pt-16 pb-12">
      <SwissContainer>
        <div className="text-center space-y-8">
          <div className="space-y-4">
            <SwissHeading level={1} align="center" className="max-w-4xl mx-auto">
              Everything You Need Is
              <br />
              <span className="text-muted-foreground">Just a Conversation Away</span>
            </SwissHeading>
            
            <SwissText size="xl" color="muted" className="max-w-2xl mx-auto">
              Your intelligent productivity assistant. Schedule meetings, manage emails, track tasks, 
              and stay organized—all through simple conversation.
            </SwissText>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <SwissButton size="lg" onClick={onGetStarted}>
              Start Free
              <ArrowRight className="w-5 h-5" />
            </SwissButton>
            
            <SwissButton variant="outline" size="lg">
              View Demo
            </SwissButton>
          </div>

          {/* Status Indicator */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-muted rounded-sm text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            {isAuthenticated ? 'Account Connected' : 'Ready to Connect'}
          </div>
        </div>
      </SwissContainer>
    </SwissSection>
  )
}
