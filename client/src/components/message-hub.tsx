import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { format } from "date-fns";
import { Mail, Send, Archive, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: number;
  senderId: number;
  recipientId: number;
  subject: string;
  content: string;
  status: "unread" | "read" | "archived";
  category: "general" | "appointment" | "prescription" | "urgent" | "test_results";
  createdAt: string;
  readAt?: string;
}

interface ComposeMessageData {
  recipientId: number;
  subject: string;
  content: string;
  category: Message["category"];
}

export default function MessageHub() {
  const [folder, setFolder] = useState<"inbox" | "sent">("inbox");
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: messages, isLoading } = useQuery<Message[]>({
    queryKey: ["/api/messages", folder],
    queryFn: async () => {
      const res = await fetch(`/api/messages?folder=${folder}`);
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (data: ComposeMessageData) => {
      const res = await fetch("/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/messages"] });
      toast({
        title: "Message Sent",
        description: "Your message has been sent successfully.",
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const updateMessageStatusMutation = useMutation({
    mutationFn: async ({
      messageId,
      status,
    }: {
      messageId: number;
      status: Message["status"];
    }) => {
      const res = await fetch(`/api/messages/${messageId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/messages"] });
    },
  });

  const handleSendMessage = async (data: ComposeMessageData) => {
    await sendMessageMutation.mutateAsync(data);
  };

  const handleMessageSelect = async (message: Message) => {
    setSelectedMessage(message);
    if (message.status === "unread") {
      await updateMessageStatusMutation.mutateAsync({
        messageId: message.id,
        status: "read",
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight">Messages</h2>
          <p className="text-muted-foreground">
            Secure communication with your healthcare providers
          </p>
        </div>
        <div className="flex space-x-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Mail className="mr-2 h-4 w-4" />
                Compose
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Message</DialogTitle>
                <DialogDescription>
                  Send a secure message to your healthcare provider
                </DialogDescription>
              </DialogHeader>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  handleSendMessage({
                    recipientId: parseInt(formData.get("recipientId") as string),
                    subject: formData.get("subject") as string,
                    content: formData.get("content") as string,
                    category: formData.get("category") as Message["category"],
                  });
                }}
                className="space-y-4"
              >
                <div className="space-y-2">
                  <Label htmlFor="recipientId">Recipient</Label>
                  <Select name="recipientId" required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select recipient" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Dr. Smith</SelectItem>
                      <SelectItem value="2">Dr. Johnson</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select name="category" required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="appointment">Appointment</SelectItem>
                      <SelectItem value="prescription">Prescription</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                      <SelectItem value="test_results">Test Results</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="subject">Subject</Label>
                  <Input name="subject" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content">Message</Label>
                  <Textarea name="content" required rows={5} />
                </div>
                <Button type="submit" className="w-full">
                  <Send className="mr-2 h-4 w-4" />
                  Send Message
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div className="space-y-1">
              <CardTitle>Message Center</CardTitle>
              <CardDescription>
                View and manage your secure messages
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <Button
                variant={folder === "inbox" ? "default" : "outline"}
                onClick={() => setFolder("inbox")}
              >
                Inbox
              </Button>
              <Button
                variant={folder === "sent" ? "default" : "outline"}
                onClick={() => setFolder("sent")}
              >
                Sent
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <span className="loading loading-spinner loading-lg" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {messages?.map((message) => (
                  <TableRow
                    key={message.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleMessageSelect(message)}
                  >
                    <TableCell>
                      {message.status === "unread" && (
                        <span className="flex h-2 w-2 rounded-full bg-blue-600" />
                      )}
                    </TableCell>
                    <TableCell className="font-medium">{message.subject}</TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                          message.category === "urgent"
                            ? "bg-red-100 text-red-700"
                            : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {message.category}
                      </span>
                    </TableCell>
                    <TableCell>
                      {format(new Date(message.createdAt), "PPp")}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selectedMessage && (
        <Dialog open={!!selectedMessage} onOpenChange={() => setSelectedMessage(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedMessage.subject}</DialogTitle>
              <DialogDescription>
                {format(new Date(selectedMessage.createdAt), "PPpp")}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    selectedMessage.category === "urgent"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {selectedMessage.category}
                </span>
                {selectedMessage.category === "urgent" && (
                  <div className="flex items-center space-x-2 text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">This message is marked as urgent</span>
                  </div>
                )}
              </div>
              <div className="rounded-md bg-muted p-4">
                <pre className="whitespace-pre-wrap text-sm">
                  {selectedMessage.content}
                </pre>
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() =>
                  updateMessageStatusMutation.mutateAsync({
                    messageId: selectedMessage.id,
                    status: "archived",
                  })
                }
              >
                <Archive className="mr-2 h-4 w-4" />
                Archive
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
