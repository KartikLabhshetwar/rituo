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
    <SwissSection className="pt-24 pb-32 min-h-[85vh] flex items-center relative overflow-hidden">
      {/* Background gradient for visual depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted/20 pointer-events-none" />
      
      <SwissContainer maxWidth="full" className="relative z-10">
        <div className="text-center space-y-12 max-w-5xl mx-auto">
          <div className="space-y-6">
            <SwissHeading level={1} align="center" className="max-w-4xl mx-auto">
              Everything You Need Is
              <br />
              <span className="text-muted-foreground">Just a Conversation Away</span>
            </SwissHeading>
            
            <SwissText size="xl" color="muted" className="max-w-3xl mx-auto text-lg leading-relaxed">
              Your intelligent productivity assistant. Schedule meetings, manage emails, track tasks, 
              and stay organized—all through simple conversation.
            </SwissText>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <SwissButton size="xl" onClick={onGetStarted} className="px-8 py-4">
              Start Free
              <ArrowRight className="w-5 h-5" />
            </SwissButton>
            
            <SwissButton variant="outline" size="xl" className="px-8 py-4">
              View Demo
            </SwissButton>
          </div>

          {/* Status Indicator */}
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-muted/50 backdrop-blur-sm rounded-sm text-sm text-muted-foreground border border-border/50">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            {isAuthenticated ? 'Account Connected' : 'Ready to Connect'}
          </div>
        </div>
      </SwissContainer>
    </SwissSection>
  )
}
