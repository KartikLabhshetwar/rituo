"use client"

import { SwissContainer, SwissSection, SwissGrid, SwissCard, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { Calendar, Mail, CheckSquare } from "lucide-react"

export function FeaturesSection() {
  const features = [
    {
      icon: Calendar,
      title: "Smart Calendar",
      description: "Schedule meetings, manage events, and stay organized with intelligent calendar automation."
    },
    {
      icon: Mail,
      title: "Email Management", 
      description: "Compose, send, and organize emails with AI-powered assistance and smart filtering."
    },
    {
      icon: CheckSquare,
      title: "Task Automation",
      description: "Create, update, and track tasks seamlessly across all your Google Workspace tools."
    }
  ]

  return (
    <SwissSection background="muted">
      <SwissContainer>
        <div className="text-center space-y-12">
          <div className="space-y-4">
            <SwissHeading level={2} align="center">
              Everything you need
            </SwissHeading>
            <SwissText size="lg" color="muted" className="max-w-2xl mx-auto">
              Powerful integrations designed with Swiss precision and minimalist philosophy.
            </SwissText>
          </div>

          <SwissGrid columns={3} gap="lg">
            {features.map((feature, index) => {
              const IconComponent = feature.icon
              return (
                <SwissCard key={index} variant="outlined" className="text-center space-y-4">
                  <div className="w-12 h-12 bg-foreground rounded-sm flex items-center justify-center mx-auto">
                    <IconComponent className="w-6 h-6 text-background" />
                  </div>
                  <div className="space-y-2">
                    <SwissHeading level={4}>{feature.title}</SwissHeading>
                    <SwissText size="sm" color="muted">
                      {feature.description}
                    </SwissText>
                  </div>
                </SwissCard>
              )
            })}
          </SwissGrid>
        </div>
      </SwissContainer>
    </SwissSection>
  )
}
