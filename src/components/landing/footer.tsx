"use client"

import { SwissContainer, SwissText } from "@/components/ui/swiss-layout"
import { Bot } from "lucide-react"

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <SwissContainer>
        <div className="py-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-6 h-6 bg-foreground rounded-sm flex items-center justify-center">
              <Bot className="w-4 h-4 text-background" />
            </div>
            <span className="font-semibold">Rituo</span>
          </div>
          <SwissText size="sm" color="muted">
            © {new Date().getFullYear()} Rituo. All rights reserved.
          </SwissText>
        </div>
      </SwissContainer>
    </footer>
  )
}
