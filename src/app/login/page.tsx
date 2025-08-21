"use client"

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { SwissContainer, SwissCard, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { SwissButton } from "@/components/ui/swiss-button"
import { Bot, ArrowLeft, Shield, CheckCircle2 } from 'lucide-react'

interface GoogleConfig {
  client_id: string;
  callback: (response: { credential: string }) => void;
  auto_select: boolean;
  cancel_on_tap_outside: boolean;
}

declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: GoogleConfig) => void
          prompt: () => void
        }
      }
    }
  }
}

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [clientId, setClientId] = useState('')
  const [isGoogleLoaded, setIsGoogleLoaded] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('access_token')
    if (token) {
      router.push('/chat')
      return
    }

    // Get client ID from backend
    const fetchClientId = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/auth/google-config')
        if (response.ok) {
          const data = await response.json()
          setClientId(data.client_id)
        } else {
          throw new Error('Failed to fetch Google client configuration')
        }
      } catch (error) {
        console.error('Error fetching Google client config:', error)
        setError('Failed to load Google authentication configuration')
      }
    }

    fetchClientId()
  }, [router])

  useEffect(() => {
    if (!clientId) return

    const handleGoogleResponse = async (response: { credential: string }) => {
      setIsLoading(true)
      setError('')

      try {
        // Send the credential to your backend for verification
        const authResponse = await fetch('http://localhost:8000/api/auth/google', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            credential: response.credential
          })
        })

        if (authResponse.ok) {
          const data = await authResponse.json()
          
          // Store tokens and user data
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          localStorage.setItem('user', JSON.stringify(data.user))
          
          // Redirect to chat (API key setup will be handled there)
          router.push('/chat')
        } else {
          const errorData = await authResponse.json()
          throw new Error(errorData.detail || 'Authentication failed')
        }
      } catch (error) {
        console.error('Authentication error:', error)
        setError(error instanceof Error ? error.message : 'Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }

    // Load Google Identity Services script
    const loadGoogleScript = () => {
      if (document.getElementById('google-identity-script')) {
        initializeGoogle()
        return
      }

      const script = document.createElement('script')
      script.id = 'google-identity-script'
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.defer = true
      script.onload = initializeGoogle
      document.head.appendChild(script)
    }

    const initializeGoogle = () => {
      if (typeof window !== 'undefined' && window.google) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleResponse,
          auto_select: false,
          cancel_on_tap_outside: false
        })
        setIsGoogleLoaded(true)
      }
    }

    loadGoogleScript()
  }, [clientId, router])



  const handleGoogleLogin = () => {
    if (window.google && isGoogleLoaded) {
      setError('')
      window.google.accounts.id.prompt()
    } else {
      setError('Google authentication not loaded. Please refresh the page.')
    }
  }

  const handleBackToHome = () => {
    router.push('/')
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border">
        <SwissContainer maxWidth="full">
          <div className="flex items-center justify-between py-4">
            <SwissButton variant="ghost" onClick={handleBackToHome}>
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </SwissButton>
            
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-foreground rounded-sm flex items-center justify-center">
                <Bot className="w-5 h-5 text-background" />
              </div>
              <span className="text-xl font-semibold tracking-tight">Rituo</span>
            </div>
            
            <div className="w-24" /> {/* Spacer for center alignment */}
          </div>
        </SwissContainer>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-8">
          {/* Sign In Card */}
          <SwissCard variant="outlined" className="space-y-6">
            <div className="text-center space-y-2">
              <SwissHeading level={2} align="center">
                Sign in to continue
              </SwissHeading>
              <SwissText color="muted" className="text-center">
                Connect your Google account to start using Rituo
              </SwissText>
            </div>

            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-sm">
                <SwissText size="sm" className="text-destructive text-center">
                  {error}
                </SwissText>
              </div>
            )}

            <div className="space-y-4">
              <SwissButton
                size="lg"
                className="w-full"
                onClick={handleGoogleLogin}
                disabled={isLoading || !isGoogleLoaded}
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-background border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google
                  </>
                )}
              </SwissButton>

              <div className="text-center">
                <SwissText size="sm" color="muted">
                  By continuing, you agree to our terms of service
                </SwissText>
              </div>
            </div>
          </SwissCard>

          {/* Features Preview */}
          <div className="space-y-4">
            <SwissText weight="medium" className="text-center">
              What you&apos;ll get access to:
            </SwissText>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-foreground rounded-sm flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-background" />
                </div>
                <SwissText size="sm" color="muted">
                  Smart Google Calendar management
                </SwissText>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-foreground rounded-sm flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-background" />
                </div>
                <SwissText size="sm" color="muted">
                  Intelligent Gmail automation
                </SwissText>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 bg-foreground rounded-sm flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-background" />
                </div>
                <SwissText size="sm" color="muted">
                  Seamless Google Tasks integration
                </SwissText>
              </div>
            </div>
          </div>

          {/* Security Notice */}
          <SwissCard variant="outlined" className="bg-muted/30">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-foreground rounded-sm flex items-center justify-center mt-0.5">
                <Shield className="w-4 h-4 text-background" />
              </div>
              <div className="space-y-1">
                <SwissText weight="medium" size="sm">
                  Your privacy is protected
                </SwissText>
                <SwissText size="sm" color="muted">
                  We only access the Google services you explicitly authorize. Your data stays secure and private.
                </SwissText>
              </div>
            </div>
          </SwissCard>
        </div>
      </main>
    </div>
  )
}