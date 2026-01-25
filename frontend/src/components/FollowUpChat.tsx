import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatMessage, FactCheckResult, chatWithAgent } from "@/services/api";

interface FollowUpChatProps {
  factCheckResult: FactCheckResult;
}

export function FollowUpChat({ factCheckResult }: FollowUpChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'I\'ve analyzed the content for you. Feel free to ask me any questions about the results, specific claims, or request deeper analysis on any topic.',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmedInput,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatWithAgent(trimmedInput, {
        factCheckResult,
        chatHistory: messages,
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.success 
          ? response.message 
          : 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const suggestedQuestions = [
    "Which claim is most concerning?",
    "Can I trust this source overall?",
    "Explain the debt discrepancy",
  ];

  return (
    <Card className="flex flex-col h-[400px]">
      <CardHeader className="pb-3 shrink-0">
        <CardTitle className="text-lg flex items-center gap-2">
          <Bot className="h-5 w-5 text-accent" />
          Ask Follow-up Questions
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0 pt-0">
        {/* Messages area */}
        <ScrollArea className="flex-1 pr-4" ref={scrollRef}>
          <div className="space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-3 animate-fade-in",
                  message.role === 'user' && "flex-row-reverse"
                )}
              >
                <div className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                  message.role === 'assistant' 
                    ? "bg-accent/10 text-accent" 
                    : "bg-primary text-primary-foreground"
                )}>
                  {message.role === 'assistant' ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                </div>
                
                <div className={cn(
                  "flex-1 rounded-lg p-3 text-sm",
                  message.role === 'assistant' 
                    ? "bg-muted" 
                    : "bg-primary text-primary-foreground"
                )}>
                  {message.content}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 animate-fade-in">
                <div className="h-8 w-8 rounded-full flex items-center justify-center bg-accent/10 text-accent">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex-1 rounded-lg p-3 bg-muted">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Suggested questions */}
        {messages.length === 1 && (
          <div className="flex flex-wrap gap-2 py-3">
            {suggestedQuestions.map((question, i) => (
              <Button
                key={i}
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => setInput(question)}
              >
                {question}
              </Button>
            ))}
          </div>
        )}

        {/* Input form */}
        <form onSubmit={handleSubmit} className="flex gap-2 pt-3 border-t">
          <Input
            ref={inputRef}
            placeholder="Ask about the analysis..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
