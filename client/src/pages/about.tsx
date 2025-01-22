import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { Shield, Heart, Globe, Zap } from "lucide-react";

const values = [
  {
    icon: Shield,
    title: "Privacy First",
    description: "We prioritize the security and confidentiality of your medical data with state-of-the-art encryption.",
  },
  {
    icon: Heart,
    title: "Patient-Centric",
    description: "Our platform is designed around your needs, making healthcare more accessible and personalized.",
  },
  {
    icon: Globe,
    title: "Universal Access",
    description: "Breaking language barriers in healthcare with advanced medical translation services.",
  },
  {
    icon: Zap,
    title: "Innovation Driven",
    description: "Leveraging cutting-edge AI technology to provide intelligent health insights and recommendations.",
  },
];

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/10">
      {/* Navigation */}
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

      {/* About Content */}
      <div className="container mx-auto px-4 pt-32 pb-16">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h1 className="text-4xl font-bold mb-6">Revolutionizing Healthcare Through Technology</h1>
          <p className="text-xl text-muted-foreground mb-8">
            We're on a mission to make healthcare more accessible, intelligent, and personalized through
            cutting-edge AI technology and innovative solutions.
          </p>
          <div className="flex justify-center gap-4">
            <Button size="lg">Learn More</Button>
            <Button size="lg" variant="outline">Contact Us</Button>
          </div>
        </div>

        {/* Our Values */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center mb-12">Our Values</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value) => {
              const Icon = value.icon;
              return (
                <div key={value.title} className="text-center">
                  <div className="mb-4 mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{value.title}</h3>
                  <p className="text-muted-foreground">{value.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Timeline */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center mb-12">Our Journey</h2>
          <div className="max-w-3xl mx-auto space-y-8">
            <div className="relative pl-8 border-l-2 border-primary/20">
              <div className="absolute left-[-9px] top-2 h-4 w-4 rounded-full bg-primary"></div>
              <h3 className="text-xl font-semibold mb-2">2025</h3>
              <p className="text-muted-foreground">
                Launched our AI-powered healthcare platform with advanced symptom visualization and multilingual support.
              </p>
            </div>
            <div className="relative pl-8 border-l-2 border-primary/20">
              <div className="absolute left-[-9px] top-2 h-4 w-4 rounded-full bg-primary/60"></div>
              <h3 className="text-xl font-semibold mb-2">2024</h3>
              <p className="text-muted-foreground">
                Developed cutting-edge AI algorithms for health analysis and prediction.
              </p>
            </div>
            <div className="relative pl-8">
              <div className="absolute left-[-9px] top-2 h-4 w-4 rounded-full bg-primary/40"></div>
              <h3 className="text-xl font-semibold mb-2">2023</h3>
              <p className="text-muted-foreground">
                Started research and development in AI-powered healthcare solutions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
