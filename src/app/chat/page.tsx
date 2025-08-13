"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
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
import { Send, Bot } from 'lucide-react'

interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
}

export default function ChatTest() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatId, setChatId] = useState('')
  const [user, setUser] = useState<any>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const router = useRouter()

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const userData = localStorage.getItem('user')
    
    if (!token || !userData) {
      // Redirect to login if not authenticated
      router.push('/login')
      return
    }
    
    setAccessToken(token)
    setUser(JSON.parse(userData))
    setChatId(`chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  }, [router])

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
      // Call the AI API (with proper authentication)
      const response = await fetch('http://localhost:8000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
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
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Make sure the server is running on http://localhost:8000`,
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
    router.push('/login')
  }

  // Show loading while checking authentication
  if (!user || !accessToken) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b p-4">
        <h1 className="text-2xl font-bold">Chat - Google Calendar Assistant</h1>
        <div className="flex items-center justify-between">
          <p className="text-muted-foreground">
            Welcome {user?.name}! I can help you with Google Calendar, Gmail, and Tasks
          </p>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Logout
          </Button>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Chat ID: {chatId}
        </p>
      </div>

      {/* Chat Container */}
      <div className="flex-1 overflow-hidden">
        <ChatContainerRoot className="h-full p-4">
          <ChatContainerContent>
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <div className="text-muted-foreground">
                  <Bot size={48} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Start a conversation</h3>
                  <p className="text-muted-foreground">
                    Try asking me to schedule a meeting, check your calendar, or manage your tasks!
                  </p>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>• &quot;Schedule a meeting with John tomorrow at 2 PM&quot;</p>
                  <p>• &quot;What meetings do I have today?&quot;</p>
                  <p>• &quot;Create a task to review the project proposal&quot;</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <Message key={message.id}>
                    <MessageAvatar
                      src={message.role === 'user' ? '' : ''}
                      alt={message.role === 'user' ? 'User' : 'Assistant'}
                      fallback={message.role === 'user' ? 'U' : 'AI'}
                    />
                    <MessageContent
                      markdown={message.role === 'assistant'}
                      className={
                        message.role === 'user' 
                          ? 'bg-primary text-primary-foreground' 
                          : 'bg-secondary'
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
                      alt="Assistant"
                      fallback="AI"
                    />
                    <MessageContent markdown={false} className="bg-secondary">
                      <div className="flex items-center space-x-2">
                        <div className="animate-pulse">Thinking...</div>
                      </div>
                    </MessageContent>
                  </Message>
                )}
              </div>
            )}
            <ChatContainerScrollAnchor />
          </ChatContainerContent>
        </ChatContainerRoot>
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <PromptInput
          value={input}
          onValueChange={setInput}
          isLoading={isLoading}
          onSubmit={sendMessage}
          className="w-full"
        >
          <PromptInputTextarea
            placeholder="Ask me to schedule a meeting, check your calendar, or manage tasks..."
            className="min-h-[60px]"
          />
          <PromptInputActions className="p-2">
            <PromptInputAction tooltip="Send message">
              <Button
                size="sm"
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="rounded-2xl"
              >
                <Send size={16} />
              </Button>
            </PromptInputAction>
          </PromptInputActions>
        </PromptInput>
      </div>

      {/* Debug Info */}
      {process.env.NODE_ENV === 'development' && (
        <div className="border-t p-2 text-xs text-muted-foreground">
          <details>
            <summary>Debug Info</summary>
            <pre className="mt-2 text-xs">
              {JSON.stringify({ chatId, messagesCount: messages.length, isLoading }, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  )
}
