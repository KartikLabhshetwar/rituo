"use client"

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { SwissContainer, SwissCard, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { SwissButton } from "@/components/ui/swiss-button"
import { Bot, CheckCircle2, AlertCircle, ArrowRight, Loader2 } from 'lucide-react'

function OAuthSuccessContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Verifying your authentication...')
  const [progress, setProgress] = useState(0)
  const [userName, setUserName] = useState('')

  // Progress animation for loading state
  useEffect(() => {
    if (status === 'processing') {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev
          return prev + Math.random() * 15
        })
      }, 200)

      return () => clearInterval(interval)
    }
  }, [status])

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const code = searchParams.get('code')
      const tempToken = searchParams.get('temp_token')
      const error = searchParams.get('error')
      const state = searchParams.get('state')

      if (error) {
        setStatus('error')
        setMessage(`Authentication was cancelled or failed: ${error}`)
        return
      }

      // Prioritize authorization code flow (primary method)
      if (code) {
        try {
          setMessage('Exchanging authorization code...')
          setProgress(30)
          
          // Exchange authorization code for tokens via your backend
          const response = await fetch('http://localhost:8000/api/auth/google', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
              authorization_code: code,
              state: state
            }),
          })

          setProgress(60)
          setMessage('Finalizing authentication...')

          if (response.ok) {
            const data = await response.json()
            
            // Store tokens
            localStorage.setItem('access_token', data.access_token)
            if (data.refresh_token) {
              localStorage.setItem('refresh_token', data.refresh_token)
            }
            localStorage.setItem('user', JSON.stringify(data.user))
            
            setProgress(100)
            setUserName(data.user?.name || data.user?.email || 'User')
            setStatus('success')
            setMessage('Welcome to Rituo! Your account is ready.')
            
            // Redirect to chat after showing success
            setTimeout(() => {
              router.push('/chat')
            }, 2500)
          } else {
            const errorData = await response.json()
            setStatus('error')
            setMessage(errorData.detail || 'Authentication failed. Please try again.')
          }
        } catch (error) {
          setStatus('error')
          setMessage('Network error. Please check your connection and try again.')
          console.error('OAuth callback error:', error)
        }
        return
      }

      // Fallback to temp token (MCP server flow)
      if (tempToken) {
        try {
          setMessage('Validating MCP server token...')
          setProgress(40)
          
          // Exchange temp token with backend
          const response = await fetch('http://localhost:8000/api/auth/google', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
              temp_token: tempToken
            }),
          })

          setProgress(80)

          if (response.ok) {
            const data = await response.json()
            
            // Store tokens
            localStorage.setItem('access_token', data.access_token)
            if (data.refresh_token) {
              localStorage.setItem('refresh_token', data.refresh_token)
            }
            localStorage.setItem('user', JSON.stringify(data.user))
            
            setProgress(100)
            setUserName(data.user?.name || data.user?.email || 'User')
            setStatus('success')
            setMessage('MCP server authentication successful!')
            
            // Redirect to chat after showing success
            setTimeout(() => {
              router.push('/chat')
            }, 2500)
          } else {
            const errorData = await response.json()
            setStatus('error')
            setMessage(errorData.detail || 'MCP authentication failed')
          }
        } catch (error) {
          setStatus('error')
          setMessage('Network error during MCP authentication')
          console.error('MCP OAuth callback error:', error)
        }
        return
      }

      // No valid authentication parameters
      setStatus('error')
      setMessage('No valid authentication credentials received. Please try signing in again.')
    }

    // Add slight delay to show initial loading state
    setTimeout(handleOAuthCallback, 500)
  }, [searchParams, router])

  const handleTryAgain = () => {
    router.push('/login')
  }

  const handleGoToChat = () => {
    router.push('/chat')
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border">
        <SwissContainer maxWidth="full">
          <div className="flex items-center justify-center py-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-foreground rounded-sm flex items-center justify-center">
                <Bot className="w-5 h-5 text-background" />
              </div>
              <span className="text-xl font-semibold tracking-tight">Rituo</span>
            </div>
          </div>
        </SwissContainer>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <SwissCard variant="outlined" className="space-y-8 text-center">
            
            {/* Processing State */}
            {status === 'processing' && (
              <>
                <div className="space-y-4">
                  <div className="w-16 h-16 mx-auto bg-muted rounded-sm flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-foreground animate-spin" />
                  </div>
                  
                  <div className="space-y-2">
                    <SwissHeading level={2} align="center">
                      Authenticating
                    </SwissHeading>
                    <SwissText color="muted" className="text-center">
                      {message}
                    </SwissText>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="bg-foreground h-2 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <SwissText size="sm" color="muted" className="text-center">
                    {Math.round(progress)}% complete
                  </SwissText>
                </div>
              </>
            )}

            {/* Success State */}
            {status === 'success' && (
              <>
                <div className="space-y-4">
                  <div className="w-16 h-16 mx-auto bg-foreground rounded-sm flex items-center justify-center animate-pulse">
                    <CheckCircle2 className="w-8 h-8 text-background" />
                  </div>
                  
                  <div className="space-y-3">
                    <SwissHeading level={2} align="center" className="text-foreground">
                      Welcome, {userName}!
                    </SwissHeading>
                    <SwissText color="muted" className="text-center leading-relaxed">
                      {message}
                    </SwissText>
                    <SwissText size="sm" color="muted" className="text-center">
                      You&apos;ll be redirected to your dashboard shortly
                    </SwissText>
                  </div>
                </div>

                {/* Success Animation Progress */}
                <div className="space-y-3">
                  <div className="w-full bg-muted rounded-full h-1">
                    <div className="bg-foreground h-1 rounded-full w-full animate-pulse" />
                  </div>
                  
                  <SwissButton 
                    size="sm" 
                    variant="ghost" 
                    onClick={handleGoToChat}
                    className="w-full"
                  >
                    <span>Continue to Rituo</span>
                    <ArrowRight className="w-4 h-4" />
                  </SwissButton>
                </div>
              </>
            )}

            {/* Error State */}
            {status === 'error' && (
              <>
                <div className="space-y-4">
                  <div className="w-16 h-16 mx-auto bg-destructive rounded-sm flex items-center justify-center">
                    <AlertCircle className="w-8 h-8 text-destructive-foreground" />
                  </div>
                  
                  <div className="space-y-3">
                    <SwissHeading level={2} align="center" className="text-destructive">
                      Authentication Failed
                    </SwissHeading>
                    <SwissText color="muted" className="text-center leading-relaxed">
                      {message}
                    </SwissText>
                  </div>
                </div>

                <div className="space-y-3">
                  <SwissButton 
                    size="lg" 
                    onClick={handleTryAgain}
                    className="w-full"
                  >
                    Try Again
                  </SwissButton>
                  
                  <SwissButton 
                    variant="ghost" 
                    size="sm"
                    onClick={() => router.push('/')}
                    className="w-full"
                  >
                    Back to Home
                  </SwissButton>
                </div>
              </>
            )}

          </SwissCard>

          {/* Footer Message */}
          <div className="mt-6 text-center">
            <SwissText size="sm" color="muted">
              Having trouble? <button 
                onClick={() => router.push('/login')} 
                className="underline hover:no-underline text-foreground"
              >
                Try signing in again
              </button>
            </SwissText>
          </div>
        </div>
      </main>
    </div>
  )
}

// Loading Fallback Component
function LoadingFallback() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b border-border">
        <SwissContainer maxWidth="full">
          <div className="flex items-center justify-center py-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-foreground rounded-sm flex items-center justify-center">
                <Bot className="w-5 h-5 text-background" />
              </div>
              <span className="text-xl font-semibold tracking-tight">Rituo</span>
            </div>
          </div>
        </SwissContainer>
      </header>

      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <SwissCard variant="outlined" className="space-y-6 text-center">
            <div className="w-16 h-16 mx-auto bg-muted rounded-sm flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-foreground animate-spin" />
            </div>
            <SwissHeading level={2} align="center">
              Initializing...
            </SwissHeading>
          </SwissCard>
        </div>
      </main>
    </div>
  )
}

export default function OAuthSuccess() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <OAuthSuccessContent />
    </Suspense>
  )
}