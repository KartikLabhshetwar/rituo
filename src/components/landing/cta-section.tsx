"use client"

import { SwissContainer, SwissSection, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { SwissButton } from "@/components/ui/swiss-button"
import { ArrowRight } from "lucide-react"

interface CTASectionProps {
  isAuthenticated: boolean
  onGetStarted: () => void
}

export function CTASection({ isAuthenticated, onGetStarted }: CTASectionProps) {
  return (
    <SwissSection className="py-24 relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-gradient-to-t from-muted/10 to-background pointer-events-none" />
      
      <SwissContainer maxWidth="full" className="relative z-10">
        <div className="text-center space-y-10 max-w-3xl mx-auto">
          <div className="space-y-6">
            <SwissHeading level={2} align="center" className="text-4xl">
              Ready to get started?
            </SwissHeading>
            <SwissText size="xl" color="muted" className="text-xl leading-relaxed">
              Join thousands of users who trust Rituo to manage their Google Workspace efficiently.
            </SwissText>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <SwissButton size="xl" onClick={onGetStarted} className="px-10 py-4">
              {isAuthenticated ? 'Complete Setup' : 'Get Started Free'}
              <ArrowRight className="w-5 h-5" />
            </SwissButton>
          </div>

          <SwissText size="sm" color="muted" className="text-base">
            No credit card required • Set up in under 2 minutes
          </SwissText>
        </div>
      </SwissContainer>
    </SwissSection>
  )
}
