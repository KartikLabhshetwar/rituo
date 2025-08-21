"use client"

import { useState, useEffect } from 'react'
import { SwissButton } from '@/components/ui/swiss-button'
import { useRouter } from 'next/navigation'
import { ApiKeySetup } from '@/components/ui/api-key-setup'
import { 
  ChatContainerRoot, 
  ChatContainerContent, 
  ChatContainerScrollAnchor 
} from '@/components/ui/chat-container'
import { 
  Message, 
  MessageAvatar, 
  MessageContent 
} from '@/components/ui/message'
import { 
  PromptInput, 
  PromptInputTextarea, 
  PromptInputActions,
  PromptInputAction 
} from '@/components/ui/prompt-input'
import { Send, Bot, Key, LogOut, Loader2 } from 'lucide-react'

interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatId, setChatId] = useState('')
  const [user, setUser] = useState<{ name: string; email: string } | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [showApiKeySetup, setShowApiKeySetup] = useState(false)
  const [hasApiKey, setHasApiKey] = useState(false)
  const router = useRouter()

  // Check authentication and API key on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    const apiKey = localStorage.getItem('groq_api_key')
    
    if (!token || !userData) {
      router.push('/login')
      return
    }
    
    setAccessToken(token)
    setUser(JSON.parse(userData))
    setHasApiKey(!!apiKey)
    
    if (!apiKey) {
      setShowApiKeySetup(true)
    } else {
      createChatSession(token)
    }
  }, [router])

  const createChatSession = async (token: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/chats/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: 'New Chat'
        })
      })

      if (response.ok) {
        const chatSession = await response.json()
        setChatId(chatSession.id)
      } else {
        setChatId(`chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
      }
    } catch {
      setChatId(`chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      content: input.trim(),
      role: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const apiKey = localStorage.getItem('groq_api_key')
      const response = await fetch('http://localhost:8000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
          'X-Groq-API-Key': apiKey || '', // Send user's API key
        },
        body: JSON.stringify({
          message: userMessage.content,
          chat_id: chatId,
          context: {}
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const aiResponse = await response.json()
      
      const aiMessage: ChatMessage = {
        id: aiResponse.message_id,
        content: aiResponse.response,
        role: 'assistant',
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your API key and try again.`,
        role: 'assistant',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token') 
    localStorage.removeItem('user')
    localStorage.removeItem('groq_api_key')
    router.push('/login')
  }

  const handleApiKeySetupComplete = () => {
    setShowApiKeySetup(false)
    setHasApiKey(true)
    if (accessToken) {
      createChatSession(accessToken)
    }
  }

  // Show API key setup if needed
  if (showApiKeySetup) {
    return <ApiKeySetup onComplete={handleApiKeySetupComplete} />
  }

  // Show loading while checking authentication
  if (!user || !accessToken) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header - Swiss Design: Clean, minimal, functional */}
      <header className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-foreground rounded-sm flex items-center justify-center">
                <Bot className="w-5 h-5 text-background" />
              </div>
              <div>
                <h1 className="text-lg font-semibold tracking-tight">Rituo</h1>
                <p className="text-xs text-muted-foreground">Google Workspace Assistant</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <SwissButton
                variant="ghost"
                size="sm"
                onClick={() => setShowApiKeySetup(true)}
                className="text-muted-foreground hover:text-foreground"
              >
                <Key className="w-4 h-4" />
              </SwissButton>
              <SwissButton
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-muted-foreground hover:text-foreground"
              >
                <LogOut className="w-4 h-4" />
              </SwissButton>
            </div>
          </div>
          
          {user && (
            <div className="mt-2 text-xs text-muted-foreground">
              {user.name} • {hasApiKey ? '🟢 API Key Active' : '🔴 No API Key'}
            </div>
          )}
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full flex flex-col">
          <div className="flex-1 overflow-hidden">
            <ChatContainerRoot className="h-full">
              <ChatContainerContent className="px-4 py-6">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center space-y-8">
                    <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center">
                      <Bot className="w-8 h-8 text-muted-foreground" />
                    </div>
                    
                    <div className="space-y-3 max-w-md">
                      <h2 className="text-xl font-semibold tracking-tight">
                        Ready to assist
                      </h2>
                      <p className="text-muted-foreground text-sm leading-relaxed">
                        I can help you manage your Google Calendar, Gmail, and Tasks. 
                        Ask me anything about your workspace.
                      </p>
                    </div>

                    <div className="grid gap-2 w-full max-w-sm text-sm">
                      <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Try asking:
                      </div>
                      <div className="space-y-1 text-muted-foreground">
                        <div>• Schedule a meeting tomorrow at 2 PM</div>
                        <div>• What meetings do I have today?</div>
                        <div>• Create a task to review proposals</div>
                        <div>• Send an email to the team</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {messages.map((message) => (
                      <Message key={message.id}>
                        <MessageAvatar
                          src=""
                          alt={message.role === 'user' ? 'You' : 'Rituo'}
                          fallback={message.role === 'user' ? 'U' : 'R'}
                        />
                        <MessageContent
                          markdown={message.role === 'assistant'}
                          className={
                            message.role === 'user' 
                              ? 'bg-foreground text-background' 
                              : 'bg-muted'
                          }
                        >
                          {message.content}
                        </MessageContent>
                      </Message>
                    ))}
                    
                    {isLoading && (
                      <Message>
                        <MessageAvatar
                          src=""
                          alt="Rituo"
                          fallback="R"
                        />
                        <MessageContent markdown={false} className="bg-muted">
                          Thinking...
                        </MessageContent>
                      </Message>
                    )}
                  </div>
                )}
                <ChatContainerScrollAnchor />
              </ChatContainerContent>
            </ChatContainerRoot>
          </div>

          {/* Input Area - Swiss Design: Functional, clean lines */}
          <div className="border-t border-border bg-background/80 backdrop-blur-sm">
            <div className="px-4 py-4">
              <PromptInput
                value={input}
                onValueChange={setInput}
                isLoading={isLoading}
                onSubmit={sendMessage}
                className="w-full"
              >
                <PromptInputTextarea
                  placeholder="Ask me to schedule meetings, check calendar, manage tasks..."
                  className="min-h-[52px] resize-none border-0 shadow-none focus-visible:ring-0 text-sm"
                />
                <PromptInputActions className="p-2">
                                      <PromptInputAction tooltip="Send message">
                      <SwissButton
                        size="sm"
                        onClick={sendMessage}
                        disabled={!input.trim() || isLoading || !hasApiKey}
                        className="h-8 w-8 p-0 rounded-sm"
                      >
                        <Send className="w-4 h-4" />
                      </SwissButton>
                    </PromptInputAction>
                </PromptInputActions>
              </PromptInput>
            </div>
            
            {!hasApiKey && (
              <div className="px-4 pb-4">
                <div className="text-xs text-muted-foreground text-center">
                                  <SwissButton
                  variant="link"
                  size="sm"
                  onClick={() => setShowApiKeySetup(true)}
                  className="text-xs h-auto p-0 text-muted-foreground hover:text-foreground"
                >
                  Add API key to start chatting
                </SwissButton>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}