import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Shield, 
  Youtube, 
  FileSearch, 
  Brain, 
  CheckCircle,
  ArrowRight,
  TrendingUp,
  FileText,
  Scale
} from "lucide-react";

export default function Landing() {
  const steps = [
    {
      icon: Youtube,
      title: "Submit Content",
      description: "Paste a YouTube URL of financial content you want to verify",
    },
    {
      icon: FileSearch,
      title: "AI Analysis",
      description: "Our AI extracts claims and cross-references official documents",
    },
    {
      icon: CheckCircle,
      title: "Get Results",
      description: "Receive detailed verdicts with evidence for each claim",
    },
  ];

  const features = [
    {
      icon: TrendingUp,
      title: "Financial Focus",
      description: "Specialized in verifying claims about earnings, growth, and financial metrics",
    },
    {
      icon: FileText,
      title: "Official Sources",
      description: "Cross-references SEC filings, annual reports, and verified documents",
    },
    {
      icon: Scale,
      title: "Transparent Verdicts",
      description: "Clear explanations with evidence for every claim analyzed",
    },
  ];

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative py-20 md:py-32 overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-primary/5 pointer-events-none" />
        
        <div className="container relative">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 text-accent text-sm font-medium mb-6">
              <Shield className="h-4 w-4" />
              AI-Powered Financial Fact-Checking
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              Verify Financial Claims with{" "}
              <span className="text-accent">Confidence</span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Don't let misinformation guide your decisions. Our AI analyzes financial 
              content against official documents to separate facts from fiction.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg" className="gap-2">
                <Link to="/analyze">
                  Start Fact-Checking
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <a href="#how-it-works">Learn How It Works</a>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-muted/30">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Three simple steps to verify the credibility of any financial content
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                {/* Connector line */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-12 left-1/2 w-full h-0.5 bg-border" />
                )}
                
                <Card className="relative bg-background">
                  <CardContent className="pt-6 text-center">
                    <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-accent/10 text-accent mb-4">
                      <step.icon className="h-8 w-8" />
                    </div>
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 h-6 w-6 rounded-full bg-primary text-primary-foreground text-sm font-bold flex items-center justify-center">
                      {index + 1}
                    </div>
                    <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Built for Financial Accuracy
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Purpose-built to verify financial claims with the rigor they deserve
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-none bg-muted/30">
                <CardContent className="pt-6">
                  <div className="h-12 w-12 rounded-lg bg-accent/10 text-accent flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary text-primary-foreground">
        <div className="container text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Verify?
          </h2>
          <p className="text-primary-foreground/80 mb-8 max-w-xl mx-auto">
            Start fact-checking financial content now. It only takes a few minutes 
            to get a comprehensive analysis.
          </p>
          <Button asChild size="lg" variant="secondary" className="gap-2">
            <Link to="/analyze">
              Analyze Your First Video
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
