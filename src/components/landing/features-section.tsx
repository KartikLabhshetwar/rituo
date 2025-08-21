"use client"

import { SwissContainer, SwissSection, SwissGrid, SwissCard, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { Calendar, Mail, CheckSquare } from "lucide-react"

export function FeaturesSection() {
  const features = [
    {
      icon: Calendar,
      title: "Time Management",
      description: "\"Schedule my 1:1s for next week\" - Just tell me what you need and I'll handle your calendar instantly."
    },
    {
      icon: Mail,
      title: "Email Made Simple", 
      description: "\"Send a follow-up to yesterday's meeting\" - Compose, send, and organize emails through natural conversation."
    },
    {
      icon: CheckSquare,
      title: "Task Mastery",
      description: "\"Add a task to call the client tomorrow\" - Create, update, and track everything you need to get done."
    }
  ]

  return (
    <SwissSection background="muted">
      <SwissContainer>
        <div className="text-center space-y-12">
          <div className="space-y-4">
            <SwissHeading level={2} align="center">
              Work smarter, not harder
            </SwissHeading>
            <SwissText size="lg" color="muted" className="max-w-2xl mx-auto">
              Stop juggling apps and interfaces. Just tell me what you need to get done.
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
