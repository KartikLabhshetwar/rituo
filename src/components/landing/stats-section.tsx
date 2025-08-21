"use client"

import { SwissContainer, SwissSection, SwissGrid, SwissHeading, SwissText } from "@/components/ui/swiss-layout"

export function StatsSection() {
  const stats = [
    {
      value: "99.9%",
      label: "Uptime Reliability"
    },
    {
      value: "<100ms",
      label: "Average Response Time"
    },
    {
      value: "24/7",
      label: "Always Available"
    }
  ]

  return (
    <SwissSection background="muted" className="py-20">
      <SwissContainer maxWidth="full">
        <div className="max-w-6xl mx-auto">
          <SwissGrid columns={3} gap="lg">
            {stats.map((stat, index) => (
              <div key={index} className="text-center space-y-4 py-8">
                <SwissHeading level={2} className="text-4xl font-bold">{stat.value}</SwissHeading>
                <SwissText color="muted" className="text-lg">{stat.label}</SwissText>
              </div>
            ))}
          </SwissGrid>
        </div>
      </SwissContainer>
    </SwissSection>
  )
}
