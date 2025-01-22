import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Globe, MessageSquare, Brain, Shield, HeartPulse } from "lucide-react";

const features = [
  {
    title: "AI-Powered Symptom Visualization",
    description: "Track and visualize your symptoms over time with advanced AI analytics for better health insights.",
    icon: Activity,
  },
  {
    title: "Multilingual Medical Support",
    description: "Access medical information in multiple languages with our advanced translation system for medical terminology.",
    icon: Globe,
  },
  {
    title: "Secure Patient Communication",
    description: "Communicate with healthcare providers through our encrypted messaging system.",
    icon: MessageSquare,
  },
  {
    title: "Intelligent Health Analysis",
    description: "Get personalized health insights powered by advanced AI algorithms.",
    icon: Brain,
  },
  {
    title: "Data Privacy & Security",
    description: "Your health data is protected with state-of-the-art encryption and GDPR compliance.",
    icon: Shield,
  },
  {
    title: "Real-time Health Monitoring",
    description: "Monitor your health metrics in real-time with intelligent alerts and notifications.",
    icon: HeartPulse,
  },
];

export default function Features() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/10">
      {/* Navigation - same as home page */}
      <nav className="fixed top-0 w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50 border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              HealthAI
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost">Features</Button>
            <Button variant="ghost">Pricing</Button>
            <Link href="/symptoms">
              <Button variant="ghost">Symptoms</Button>
            </Link>
            <Button variant="ghost">About</Button>
            <Button variant="ghost">Contact</Button>
            <Button>Get Started</Button>
          </div>
        </div>
      </nav>

      {/* Features Content */}
      <div className="container mx-auto px-4 pt-32 pb-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold mb-4">Powerful Features for Better Healthcare</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Discover how our AI-powered platform revolutionizes healthcare management with cutting-edge features
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="transition-all hover:shadow-lg">
                <CardHeader>
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
