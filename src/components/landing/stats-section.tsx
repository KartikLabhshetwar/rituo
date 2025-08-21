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
    <SwissSection background="muted">
      <SwissContainer>
        <SwissGrid columns={3} gap="lg">
          {stats.map((stat, index) => (
            <div key={index} className="text-center space-y-2">
              <SwissHeading level={2}>{stat.value}</SwissHeading>
              <SwissText color="muted">{stat.label}</SwissText>
            </div>
          ))}
        </SwissGrid>
      </SwissContainer>
    </SwissSection>
  )
}
