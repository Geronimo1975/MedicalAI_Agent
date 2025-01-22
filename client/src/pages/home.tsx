import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, Cookie, Shield } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Link } from "wouter";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { AccessibilityMenu } from "@/components/ui/accessibility-menu";

const pricingPlans = [
  {
    name: "Basic Care",
    price: "$29",
    period: "per month",
    features: [
      "24/7 AI Health Assistant",
      "Symptom Checker",
      "Basic Health Recommendations",
      "Emergency Care Guidance",
      "Health Journal"
    ],
    highlighted: false
  },
  {
    name: "Professional Care",
    price: "$79",
    period: "per month",
    features: [
      "All Basic Care features",
      "Advanced AI Diagnostics",
      "Personalized Treatment Plans",
      "Mental Health Support",
      "Real-time Health Monitoring",
      "Priority Response"
    ],
    highlighted: true
  },
  {
    name: "Premium Care",
    price: "$149",
    period: "per month",
    features: [
      "All Professional Care features",
      "Family Health Management",
      "Specialist AI Consultations",
      "Genomic Analysis",
      "Preventive Care Planning",
      "24/7 Emergency Support",
      "Comprehensive Health Reports"
    ],
    highlighted: false
  }
];

export default function Home() {
  const [cookieConsent, setCookieConsent] = useState(false);
  const [gdprDialog, setGdprDialog] = useState(true);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/10">
      {/* Skip to main content link for keyboard users */}
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50 border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent cursor-pointer">
                HealthAI
              </h1>
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/features">
              <Button variant="ghost">Features</Button>
            </Link>
            <Button variant="ghost">Pricing</Button>
            <Link href="/symptoms">
              <Button variant="ghost">Symptoms</Button>
            </Link>
            <Link href="/about">
              <Button variant="ghost">About</Button>
            </Link>
            <Link href="/contact">
              <Button variant="ghost">Contact</Button>
            </Link>
            <ThemeToggle />
            <AccessibilityMenu />
            <Button>Get Started</Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="main-content" className="pt-32 pb-16 px-4" role="main" aria-label="Welcome to HealthAI">
        <div className="container mx-auto text-center">
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Your Personal AI Healthcare Assistant
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Experience the future of healthcare with our advanced AI-powered medical assistance platform.
            Get instant health insights, personalized care recommendations, and 24/7 support.
          </p>
          <div className="flex justify-center gap-4">
            <Button size="lg">Start Free Trial</Button>
            <Button size="lg" variant="outline">Learn More</Button>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-16 px-4" id="pricing">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Choose Your Care Level</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingPlans.map((plan) => (
              <Card
                key={plan.name}
                className={plan.highlighted ? "border-primary shadow-lg" : ""}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </div>
                )}
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <CardDescription>
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground"> {plan.period}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5 text-primary" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button className="w-full mt-6" variant={plan.highlighted ? "default" : "outline"}>
                    Get Started
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Enhanced Cookie Consent */}
      {!cookieConsent && (
        <div className="fixed bottom-6 w-full z-50 px-4">
          <div className="container mx-auto">
            <Card className="bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/75 shadow-lg border-primary/10">
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="hidden sm:flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary/10">
                      <Cookie className="h-6 w-6 text-primary" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-semibold leading-none tracking-tight">Cookie Preferences</h4>
                      <p className="text-sm text-muted-foreground">
                        We use cookies to enhance your experience and analyze our website traffic.
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setCookieConsent(true)}
                      className="shadow-sm hover:bg-secondary"
                    >
                      Decline All
                    </Button>
                    <Button
                      onClick={() => setCookieConsent(true)}
                      className="shadow-sm bg-primary hover:bg-primary/90"
                    >
                      Accept All
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* GDPR Dialog */}
      <Dialog open={gdprDialog} onOpenChange={setGdprDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex gap-2">
              <Shield className="h-6 w-6 text-primary" />
              Privacy Notice
            </DialogTitle>
            <DialogDescription>
              Your privacy is important to us. This platform adheres to GDPR guidelines and ensures:
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Your personal data is securely stored and encrypted</span>
              </li>
              <li className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">You have the right to access, modify, or delete your data</span>
              </li>
              <li className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">We only collect data necessary for providing our services</span>
              </li>
              <li className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <span className="text-sm">Your data is never shared with third parties without consent</span>
              </li>
            </ul>
            <Button className="w-full" onClick={() => setGdprDialog(false)}>
              I Understand
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}