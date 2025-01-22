import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageCircle, Send, X, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useMutation, useQuery } from "@tanstack/react-query";

interface Message {
  role: 'assistant' | 'user';
  content: string;
  timestamp: string;
}

interface ChatWidgetProps {
  subscriptionTier: 'basic' | 'professional' | 'premium' | null;
  isAuthenticated: boolean;
}

export function ChatWidget({ subscriptionTier, isAuthenticated }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Query to get chat history when a session exists
  const { data: chatHistory = [], isLoading: isLoadingHistory } = useQuery({
    queryKey: ['chat-history', sessionId],
    queryFn: async () => {
      if (!sessionId) return [];
      const res = await fetch(`/api/chat/session/${sessionId}`);
      if (!res.ok) throw new Error('Failed to fetch chat history');
      const data = await res.json();
      return data.messages;
    },
    enabled: !!sessionId,
  });

  // Mutation to start a new chat session
  const startSession = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/chat/session', {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to start chat session');
      return res.json();
    },
    onSuccess: (data) => {
      setSessionId(data.session_id);
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to start chat session. Please try again.",
        variant: "destructive",
      });
    },
  });

  // Mutation to send a message
  const sendMessage = useMutation({
    mutationFn: async (userMessage: string) => {
      if (!sessionId) throw new Error('No active session');
      const res = await fetch(`/api/chat/session/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to send message');
      return res.json();
    },
    onSuccess: () => {
      setMessage("");
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
    },
  });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory]);

  // Get subscription-based message limit
  const getMessageLimit = () => {
    switch (subscriptionTier) {
      case 'premium':
        return Infinity;
      case 'professional':
        return 50;
      case 'basic':
        return 10;
      default:
        return 3; // Free tier
    }
  };

  const messageCount = chatHistory.length;
  const messageLimit = getMessageLimit();
  const canSendMessage = messageCount < messageLimit;

  const handleSend = async () => {
    if (!message.trim() || !canSendMessage) return;

    if (!isAuthenticated) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to continue the conversation.",
        variant: "destructive",
      });
      return;
    }

    if (!sessionId) {
      await startSession.mutateAsync();
    }
    await sendMessage.mutateAsync(message);
  };

  if (!isOpen) {
    return (
      <Button
        className="fixed bottom-6 right-6 h-12 w-12 rounded-full p-0"
        onClick={() => setIsOpen(true)}
      >
        <MessageCircle className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 w-80 h-96 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">AI Health Assistant</CardTitle>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 rounded-full"
          onClick={() => setIsOpen(false)}
        >
          <X className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64 pr-4" ref={scrollRef}>
          {isLoadingHistory ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="space-y-4">
              {chatHistory.map((msg: Message, i: number) => (
                <div
                  key={i}
                  className={`flex ${
                    msg.role === 'assistant' ? 'justify-start' : 'justify-end'
                  }`}
                >
                  <div
                    className={`rounded-lg px-3 py-2 max-w-[80%] ${
                      msg.role === 'assistant'
                        ? 'bg-secondary text-secondary-foreground'
                        : 'bg-primary text-primary-foreground'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
      <CardFooter>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex w-full gap-2"
        >
          <Input
            placeholder={
              canSendMessage
                ? "Type your message..."
                : `Message limit reached (${messageCount}/${messageLimit})`
            }
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={!canSendMessage || sendMessage.isPending}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!message.trim() || !canSendMessage || sendMessage.isPending}
          >
            {sendMessage.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
}
