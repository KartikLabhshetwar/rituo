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
    <SwissSection>
      <SwissContainer>
        <div className="text-center space-y-8 max-w-2xl mx-auto">
          <div className="space-y-4">
            <SwissHeading level={2} align="center">
              Ready to get started?
            </SwissHeading>
            <SwissText size="lg" color="muted">
              Join thousands of users who trust Rituo to manage their Google Workspace efficiently.
            </SwissText>
          </div>

          <SwissButton size="xl" onClick={onGetStarted}>
            {isAuthenticated ? 'Complete Setup' : 'Get Started Free'}
            <ArrowRight className="w-5 h-5" />
          </SwissButton>

          <SwissText size="sm" color="muted">
            No credit card required • Set up in under 2 minutes
          </SwissText>
        </div>
      </SwissContainer>
    </SwissSection>
  )
}
