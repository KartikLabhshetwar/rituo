"use client"

import { SwissContainer, SwissSection, SwissGrid, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { Shield, Zap, Smartphone, Key } from "lucide-react"

export function BenefitsSection() {
  const benefits = [
    {
      icon: Shield,
      title: "Privacy First",
      description: "Your API keys stay in your browser. We never see your data."
    },
    {
      icon: Zap,
      title: "Lightning Fast", 
      description: "Optimized performance with instant responses and real-time updates."
    },
    {
      icon: Smartphone,
      title: "Mobile Ready",
      description: "Responsive design that works perfectly on all devices."
    }
  ]

  return (
    <SwissSection>
      <SwissContainer>
        <SwissGrid columns={2} gap="lg" className="items-center">
          <div className="space-y-6">
            <div className="space-y-4">
              <SwissHeading level={2}>
                Built for modern teams
              </SwissHeading>
              <SwissText size="lg" color="muted">
                Experience the perfect balance of powerful functionality and elegant simplicity. 
                Designed following Swiss design principles for maximum clarity and efficiency.
              </SwissText>
            </div>

            <div className="space-y-4">
              {benefits.map((benefit, index) => {
                const IconComponent = benefit.icon
                return (
                  <div key={index} className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-foreground rounded-sm flex items-center justify-center mt-0.5">
                      <IconComponent className="w-4 h-4 text-background" />
                    </div>
                    <div>
                      <SwissText weight="medium">{benefit.title}</SwissText>
                      <SwissText size="sm" color="muted">{benefit.description}</SwissText>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="bg-muted rounded-sm p-8 text-center space-y-6">
            <div className="w-16 h-16 bg-foreground rounded-sm flex items-center justify-center mx-auto">
              <Key className="w-8 h-8 text-background" />
            </div>
            <div className="space-y-2">
              <SwissHeading level={3}>Bring Your Own Key</SwissHeading>
              <SwissText color="muted">
                Use your own Groq API key for unlimited usage. No rate limits, no subscription fees.
              </SwissText>
            </div>
          </div>
        </SwissGrid>
      </SwissContainer>
    </SwissSection>
  )
}
