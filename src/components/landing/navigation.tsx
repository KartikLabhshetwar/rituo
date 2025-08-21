"use client"

import { SwissContainer } from "@/components/ui/swiss-layout"
import { SwissButton } from "@/components/ui/swiss-button"
import { Bot, ArrowRight } from "lucide-react"

interface NavigationProps {
  isAuthenticated: boolean
  onSignIn: () => void
  onGetStarted: () => void
}

export function Navigation({ isAuthenticated, onSignIn, onGetStarted }: NavigationProps) {
  return (
    <nav className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
      <SwissContainer>
        <div className="flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-foreground rounded-sm flex items-center justify-center">
              <Bot className="w-5 h-5 text-background" />
            </div>
            <span className="text-xl font-semibold tracking-tight">Rituo</span>
          </div>
          
          <div className="flex items-center gap-4">
            <SwissButton
              variant="ghost"
              size="sm"
              onClick={onSignIn}
            >
              {isAuthenticated ? 'Dashboard' : 'Sign In'}
            </SwissButton>
            <SwissButton
              size="sm"
              onClick={onGetStarted}
            >
              Get Started
              <ArrowRight className="w-4 h-4" />
            </SwissButton>
          </div>
        </div>
      </SwissContainer>
    </nav>
  )
}
