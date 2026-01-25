import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { CredibilityScore } from "@/components/CredibilityScore";
import { ClaimCard } from "@/components/ClaimCard";
import { FollowUpChat } from "@/components/FollowUpChat";
import { 
  ArrowLeft, 
  Download, 
  RefreshCw, 
  Youtube, 
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  HelpCircle
} from "lucide-react";
import { FactCheckResult, VerdictType } from "@/services/api";

interface AnalysisMetadata {
  youtubeUrl: string;
  videoTitle?: string;
  channelName?: string;
  hadPdf: boolean;
}

export default function Results() {
  const navigate = useNavigate();
  const [result, setResult] = useState<FactCheckResult | null>(null);
  const [metadata, setMetadata] = useState<AnalysisMetadata | null>(null);

  useEffect(() => {
    // Load results from session storage
    const storedResult = sessionStorage.getItem('factCheckResult');
    const storedMetadata = sessionStorage.getItem('analysisMetadata');

    if (storedResult) {
      setResult(JSON.parse(storedResult));
    }
    if (storedMetadata) {
      setMetadata(JSON.parse(storedMetadata));
    }
  }, []);

  // Redirect if no results
  useEffect(() => {
    if (!result && !sessionStorage.getItem('factCheckResult')) {
      navigate('/analyze');
    }
  }, [result, navigate]);

  if (!result) {
    return (
      <div className="container py-20 text-center">
        <p className="text-muted-foreground">Loading results...</p>
      </div>
    );
  }

  // Count verdicts
  const verdictCounts = result.claims.reduce((acc, claim) => {
    acc[claim.verdict] = (acc[claim.verdict] || 0) + 1;
    return acc;
  }, {} as Record<VerdictType, number>);

  const handleDownloadReport = () => {
    // TODO: Implement report download
    // This would generate a PDF or JSON report
    const reportData = {
      ...result,
      metadata,
      generatedAt: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fact-check-report-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleNewAnalysis = () => {
    sessionStorage.removeItem('factCheckResult');
    sessionStorage.removeItem('analysisMetadata');
    navigate('/analyze');
  };

  return (
    <div className="container py-8 md:py-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <Button asChild variant="ghost" size="sm" className="mb-2 -ml-2">
            <Link to="/analyze">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Analyze
            </Link>
          </Button>
          <h1 className="text-2xl md:text-3xl font-bold">Analysis Results</h1>
          {metadata?.videoTitle && (
            <p className="text-muted-foreground mt-1">{metadata.videoTitle}</p>
          )}
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownloadReport} className="gap-2">
            <Download className="h-4 w-4" />
            Download Report
          </Button>
          <Button variant="outline" onClick={handleNewAnalysis} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            New Analysis
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main content - 2 columns on large screens */}
        <div className="lg:col-span-2 space-y-6">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col md:flex-row items-center gap-6">
                <CredibilityScore score={result.overallScore} size="lg" />
                
                <div className="flex-1">
                  <p className="text-muted-foreground">{result.summary}</p>
                  
                  {/* Metadata */}
                  <div className="flex flex-wrap gap-4 mt-4 text-sm">
                    {metadata?.channelName && (
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Youtube className="h-4 w-4" />
                        {metadata.channelName}
                      </div>
                    )}
                    {metadata?.hadPdf && (
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        Reference PDF included
                      </div>
                    )}
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      {new Date(result.analyzedAt).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Verdict breakdown */}
              <div>
                <h4 className="text-sm font-medium mb-3">Verdict Breakdown</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-success/10">
                    <CheckCircle className="h-5 w-5 text-success" />
                    <div>
                      <p className="text-lg font-bold text-success">{verdictCounts.true || 0}</p>
                      <p className="text-xs text-muted-foreground">True</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10">
                    <XCircle className="h-5 w-5 text-destructive" />
                    <div>
                      <p className="text-lg font-bold text-destructive">{verdictCounts.false || 0}</p>
                      <p className="text-xs text-muted-foreground">False</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-warning/10">
                    <AlertCircle className="h-5 w-5 text-warning" />
                    <div>
                      <p className="text-lg font-bold text-warning">{verdictCounts.partial || 0}</p>
                      <p className="text-xs text-muted-foreground">Partial</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-muted">
                    <HelpCircle className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-lg font-bold">{verdictCounts.unverifiable || 0}</p>
                      <p className="text-xs text-muted-foreground">Unverifiable</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Claims List */}
          <div>
            <h2 className="text-xl font-semibold mb-4">
              Analyzed Claims ({result.claims.length})
            </h2>
            <div className="space-y-4">
              {result.claims.map((claim, index) => (
                <ClaimCard key={claim.id} claim={claim} index={index} />
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar - Chat */}
        <div className="lg:col-span-1">
          <div className="sticky top-20">
            <FollowUpChat factCheckResult={result} />
          </div>
        </div>
      </div>
    </div>
  );
}
