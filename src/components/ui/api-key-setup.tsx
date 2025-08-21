"use client"

import { useState, useEffect } from 'react'
import { SwissContainer, SwissCard, SwissHeading, SwissText } from "@/components/ui/swiss-layout"
import { SwissButton } from "@/components/ui/swiss-button"
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, Key, ExternalLink, Check, X, ArrowLeft, Bot } from 'lucide-react'

interface ApiKeySetupProps {
  onComplete: () => void
  onSkip?: () => void
}

export function ApiKeySetup({ onComplete, onSkip }: ApiKeySetupProps) {
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<'success' | 'error' | null>(null)
  const [error, setError] = useState('')

  // Check if user already has an API key
  useEffect(() => {
    const existingKey = localStorage.getItem('groq_api_key')
    if (existingKey) {
      setApiKey(existingKey)
      setValidationResult('success')
    }
  }, [])

  const validateApiKey = async (key: string) => {
    if (!key.trim()) {
      setError('API key is required')
      return false
    }

    if (!key.startsWith('gsk_')) {
      setError('Invalid Groq API key format. Keys should start with "gsk_"')
      return false
    }

    setIsValidating(true)
    setError('')

    try {
      // Test the API key by making a simple request
      const response = await fetch('https://api.groq.com/openai/v1/models', {
        headers: {
          'Authorization': `Bearer ${key}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setValidationResult('success')
        return true
      } else {
        setError('Invalid API key or insufficient permissions')
        setValidationResult('error')
        return false
      }
    } catch {
      setError('Unable to validate API key. Please check your internet connection.')
      setValidationResult('error')
      return false
    } finally {
      setIsValidating(false)
    }
  }

  const handleSave = async () => {
    const isValid = await validateApiKey(apiKey)
    if (isValid) {
      localStorage.setItem('groq_api_key', apiKey)
      onComplete()
    }
  }

  const handleRemove = () => {
    localStorage.removeItem('groq_api_key')
    setApiKey('')
    setValidationResult(null)
    setError('')
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border">
        <SwissContainer maxWidth="full">
          <div className="flex items-center justify-between py-4">
            <SwissButton variant="ghost" onClick={onSkip}>
              <ArrowLeft className="w-4 h-4" />
              Back to Chat
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
          <SwissCard variant="outlined" className="space-y-6">
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-foreground rounded-sm flex items-center justify-center">
                <Key className="w-6 h-6 text-background" />
              </div>
              <div className="space-y-2">
                <SwissHeading level={2} align="center">API Key Setup</SwissHeading>
                <SwissText color="muted" className="text-center">
                  Bring your own Groq API key to get started
                </SwissText>
              </div>
            </div>
            {/* Instructions */}
            <div className="space-y-3">
              <SwissText weight="medium">How to get your Groq API key:</SwissText>
              <ol className="list-decimal list-inside space-y-1">
                <SwissText size="sm" color="muted" className="list-item">
                  Visit <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" className="text-foreground hover:underline inline-flex items-center gap-1">console.groq.com <ExternalLink className="w-3 h-3" /></a>
                </SwissText>
                <SwissText size="sm" color="muted" className="list-item">Sign up or log in to your account</SwissText>
                <SwissText size="sm" color="muted" className="list-item">Navigate to API Keys section</SwissText>
                <SwissText size="sm" color="muted" className="list-item">Create a new API key</SwissText>
                <SwissText size="sm" color="muted" className="list-item">Copy and paste it below</SwissText>
              </ol>
            </div>

          {/* API Key Input */}
          <div className="space-y-2">
            <Label htmlFor="api-key" className="text-sm font-medium">
              Groq API Key
            </Label>
            <div className="relative">
              <Input
                id="api-key"
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value)
                  setValidationResult(null)
                  setError('')
                }}
                placeholder="gsk_..."
                className="pr-20 font-mono text-sm"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                {validationResult === 'success' && (
                  <Check className="w-4 h-4 text-green-600" />
                )}
                {validationResult === 'error' && (
                  <X className="w-4 h-4 text-red-600" />
                )}
                <SwissButton
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  onClick={() => setShowKey(!showKey)}
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </SwissButton>
              </div>
            </div>
          </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-sm">
                <SwissText size="sm" className="text-destructive">
                  {error}
                </SwissText>
              </div>
            )}

            {/* Success Message */}
            {validationResult === 'success' && !error && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-sm flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                <SwissText size="sm" className="text-green-800">
                  API key is valid and ready to use!
                </SwissText>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col gap-3">
              <SwissButton
                size="lg"
                onClick={handleSave}
                disabled={!apiKey.trim() || isValidating}
                className="w-full"
              >
                {isValidating ? 'Validating...' : validationResult === 'success' ? 'Save & Continue' : 'Validate & Save'}
              </SwissButton>
              
              {validationResult === 'success' && (
                <SwissButton
                  variant="outline"
                  onClick={handleRemove}
                  className="w-full"
                >
                  Remove API Key
                </SwissButton>
              )}
              
              {onSkip && (
                <SwissButton
                  variant="ghost"
                  onClick={onSkip}
                  className="w-full"
                >
                  Skip for now
                </SwissButton>
              )}
            </div>

            {/* Privacy Note */}
            <SwissCard variant="outlined" className="bg-muted/30 text-center space-y-1">
              <SwissText size="sm" color="muted">
                🔒 Your API key is stored locally in your browser
              </SwissText>
              <SwissText size="sm" color="muted">
                We never send it to our servers
              </SwissText>
            </SwissCard>
          </SwissCard>
        </div>
      </main>
    </div>
  )
}
