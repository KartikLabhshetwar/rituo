"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Debug() {
  const [debugInfo, setDebugInfo] = useState<any>({})
  const [backendHealth, setBackendHealth] = useState<string>('checking...')

  useEffect(() => {
    // Check environment
    const info = {
      location: window.location.href,
      origin: window.location.origin,
      userAgent: navigator.userAgent,
      localStorage: {
        access_token: !!localStorage.getItem('access_token'),
        refresh_token: !!localStorage.getItem('refresh_token'),
        user: !!localStorage.getItem('user'),
      }
    }
    setDebugInfo(info)

    // Test backend connection
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setBackendHealth('✅ Connected: ' + JSON.stringify(data)))
      .catch(err => setBackendHealth('❌ Failed: ' + err.message))
  }, [])

  const testGoogleScript = () => {
    console.log('Google script test:', {
      googleAvailable: !!window.google,
      googleAccounts: !!(window as any).google?.accounts,
      googleId: !!(window as any).google?.accounts?.id,
    })
  }

  const clearStorage = () => {
    localStorage.clear()
    alert('Storage cleared!')
  }

  const testBackendAuth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/check', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      })
      const data = await response.json()
      alert('Auth check: ' + JSON.stringify(data, null, 2))
    } catch (err) {
      alert('Auth check failed: ' + err.message)
    }
  }

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Debug Information</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Environment Info</h2>
            <pre className="text-sm bg-gray-100 p-3 rounded overflow-auto">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Backend Status</h2>
            <p className="mb-4">{backendHealth}</p>
            
            <div className="space-y-2">
              <Button onClick={testGoogleScript} className="w-full">
                Test Google Script
              </Button>
              <Button onClick={testBackendAuth} className="w-full">
                Test Backend Auth
              </Button>
              <Button onClick={clearStorage} variant="destructive" className="w-full">
                Clear Storage
              </Button>
            </div>
          </div>
        </div>
        
        <div className="mt-6 bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">OAuth Configuration</h2>
          <div className="space-y-2 text-sm">
            <div><strong>Client ID:</strong> 190623858377-ofj6om63igqeta8e7qo98l3jk39gv37h.apps.googleusercontent.com</div>
            <div><strong>Expected Origins:</strong></div>
            <ul className="list-disc list-inside ml-4">
              <li>http://localhost:3000</li>
              <li>http://127.0.0.1:3000</li>
            </ul>
            <div className="mt-4">
              <strong>Steps to fix "Can't continue with google.com" error:</strong>
              <ol className="list-decimal list-inside ml-4 space-y-1">
                <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank" className="text-blue-600 underline">Google Cloud Console</a></li>
                <li>Select your OAuth client</li>
                <li>Add authorized JavaScript origins above</li>
                <li>Save and wait 5-10 minutes</li>
                <li>Clear browser cache and try again</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
