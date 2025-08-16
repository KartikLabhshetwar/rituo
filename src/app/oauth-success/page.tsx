"use client"

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

export default function OAuthSuccess() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const handleOAuthCallback = async () => {
      const code = searchParams.get('code')
      const tempToken = searchParams.get('temp_token')
      const user = searchParams.get('user')
      const error = searchParams.get('error')
      const state = searchParams.get('state')

      if (error) {
        setStatus('error')
        setMessage(`Authentication failed: ${error}`)
        return
      }

      // Prioritize temp token (new MCP server flow) over authorization code
      if (tempToken) {
        try {
          setMessage('Completing MCP server authentication...')
          
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

          if (response.ok) {
            const data = await response.json()
            
            // Store tokens
            localStorage.setItem('access_token', data.access_token)
            if (data.refresh_token) {
              localStorage.setItem('refresh_token', data.refresh_token)
            }
            localStorage.setItem('user', JSON.stringify(data.user))
            
            setStatus('success')
            setMessage('Successfully authenticated via MCP server!')
            
            // Redirect to chat after 2 seconds
            setTimeout(() => {
              router.push('/chat')
            }, 2000)
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

      // Fallback to authorization code flow (legacy)
      if (code) {
        try {
          setMessage('Processing authorization code...')
          
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

          if (response.ok) {
            const data = await response.json()
            
            // Store tokens
            localStorage.setItem('access_token', data.access_token)
            if (data.refresh_token) {
              localStorage.setItem('refresh_token', data.refresh_token)
            }
            localStorage.setItem('user', JSON.stringify(data.user))
            
            setStatus('success')
            setMessage('Successfully authenticated!')
            
            // Redirect to chat after 2 seconds
            setTimeout(() => {
              router.push('/chat')
            }, 2000)
          } else {
            const errorData = await response.json()
            setStatus('error')
            setMessage(errorData.detail || 'Authentication failed')
          }
        } catch (error) {
          setStatus('error')
          setMessage('Network error during authentication')
          console.error('OAuth callback error:', error)
        }
        return
      }

      // No valid authentication parameters
      setStatus('error')
      setMessage('No valid authentication credentials received')
    }

    handleOAuthCallback()
  }, [searchParams, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8 p-8 text-center bg-white rounded-lg shadow-lg">
        {status === 'processing' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <h2 className="text-xl font-semibold text-gray-900">Processing Authentication...</h2>
            <p className="text-gray-600">Please wait while we complete your sign-in</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="w-12 h-12 mx-auto bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-green-900">Success!</h2>
            <p className="text-green-700">{message}</p>
            <p className="text-sm text-gray-600">Redirecting to chat...</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="w-12 h-12 mx-auto bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-red-900">Authentication Failed</h2>
            <p className="text-red-700">{message}</p>
            <button 
              onClick={() => router.push('/login')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
