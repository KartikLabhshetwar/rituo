"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'

declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: any) => void
          prompt: () => void
        }
      }
    }
  }
}

export default function Login() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const initializeGoogleSignIn = () => {
    console.log('=== Initializing Google Sign-In ===')
    console.log('Checking if window.google is available:', !!window.google)
    
    if (window.google) {
      console.log('Initializing Google Identity Services...')
      try {
        window.google.accounts.id.initialize({
          client_id: '190623858377-ofj6om63igqeta8e7qo98l3jk39gv37h.apps.googleusercontent.com',
          callback: handleGoogleSignIn,
          auto_select: false,
          cancel_on_tap_outside: false,
        })
        console.log('Google Identity Services initialized successfully')
      } catch (error) {
        console.error('Error initializing Google Identity Services:', error)
        setError('Failed to initialize Google Sign-In. Please refresh the page and try again.')
      }
    } else {
      console.error('window.google is not available')
      setError('Google Sign-In not available. Please refresh the page and try again.')
    }
  }

  useEffect(() => {
    console.log('=== Login Component Mounted ===')
    console.log('Loading Google Identity Services script...')
    
    // Load Google Identity Services
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => {
      console.log('Google Identity Services script loaded successfully')
      initializeGoogleSignIn()
    }
    script.onerror = () => {
      console.error('Failed to load Google Identity Services script')
      setError('Failed to load Google Sign-In. Please refresh the page.')
    }
    document.body.appendChild(script)

    return () => {
      console.log('Cleaning up Google Identity Services script')
      try {
        document.body.removeChild(script)
      } catch (e) {
        console.warn('Error removing script:', e)
      }
    }
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const handleGoogleSignIn = async (response: { credential: string }) => {
    console.log('=== Google Sign-In Callback Triggered ===')
    console.log('Credential received, length:', response.credential?.length)
    console.log('Credential (first 50 chars):', response.credential?.substring(0, 50))
    
    if (!response.credential) {
      console.error('No credential received from Google')
      setError('Authentication failed: No credential received from Google')
      return
    }
    
    setIsLoading(true)
    setError('')

    try {
      console.log('Sending authentication request to backend...')
      console.log('Backend URL: http://localhost:8000/api/auth/google')
      
      // Send the Google token to your backend
      const authResponse = await fetch('http://localhost:8000/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          token: response.credential,
        }),
      })

      console.log('Auth response status:', authResponse.status)
      console.log('Auth response headers:', Object.fromEntries(authResponse.headers.entries()))

      if (!authResponse.ok) {
        const errorText = await authResponse.text()
        console.error('Authentication failed with status:', authResponse.status)
        console.error('Error response:', errorText)
        
        let errorMessage = 'Authentication failed'
        try {
          const errorData = JSON.parse(errorText)
          errorMessage = errorData.detail || errorMessage
        } catch {
          errorMessage = `${errorMessage}: ${authResponse.status} - ${errorText}`
        }
        
        throw new Error(errorMessage)
      }

      console.log('Authentication successful, parsing response...')
      const authData = await authResponse.json()
      console.log('Auth data received:', {
        ...authData,
        access_token: authData.access_token?.substring(0, 20) + '...',
        refresh_token: authData.refresh_token?.substring(0, 20) + '...'
      })
      
      // Validate response structure
      if (!authData.access_token || !authData.user) {
        throw new Error('Invalid response from server: missing required data')
      }
      
      // Store tokens in localStorage (in production, consider more secure storage)
      console.log('Storing tokens and user data in localStorage...')
      localStorage.setItem('access_token', authData.access_token)
      if (authData.refresh_token) {
        localStorage.setItem('refresh_token', authData.refresh_token)
      }
      localStorage.setItem('user', JSON.stringify(authData.user))
      console.log('Tokens and user data stored successfully')

      // Redirect to chat
      console.log('Redirecting to chat page...')
      router.push('/chat')

    } catch (error) {
      console.error('=== Login Error ===')
      console.error('Error details:', error)
      console.error('Error message:', error.message)
      console.error('Error stack:', error.stack)
      setError(`Login failed: ${error.message}`)
    } finally {
      setIsLoading(false)
      console.log('=== Google Sign-In Process Completed ===')
    }
  }

  const handleGoogleLogin = () => {
    console.log('=== Manual Google Login Button Clicked ===')
    console.log('Checking if window.google is available:', !!window.google)
    
    if (window.google) {
      console.log('Triggering Google prompt...')
      try {
        window.google.accounts.id.prompt()
        console.log('Google prompt triggered successfully')
      } catch (error) {
        console.error('Error triggering Google prompt:', error)
        setError('Failed to show Google Sign-In. Please refresh the page.')
      }
    } else {
      console.error('Google Sign-In not loaded')
      setError('Google Sign-In not loaded. Please refresh the page.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to Rituo
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Your AI assistant for Google Workspace
          </p>
        </div>

        <div className="mt-8 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <div className="text-center space-y-4">
            <p className="text-gray-600">
              Sign in with your Google account to access your calendar, email, and tasks.
            </p>

            <Button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-900 border border-gray-300"
              size="lg"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900"></div>
              ) : (
                <>
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Sign in with Google
                </>
              )}
            </Button>

            <div className="mt-6 text-xs text-gray-500 text-center">
              <p>
                By signing in, you agree to our terms of service and privacy policy.
                <br />
                We&apos;ll access your Google Calendar, Gmail, and Tasks to provide AI assistance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
