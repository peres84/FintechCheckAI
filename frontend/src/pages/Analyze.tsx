import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { YouTubeInput } from "@/components/YouTubeInput";
import { PDFUploader } from "@/components/PDFUploader";
import { LoadingAnalysis, AnalysisStep } from "@/components/LoadingAnalysis";
import { ArrowRight, Loader2 } from "lucide-react";
import { 
  isValidYouTubeUrl, 
  verifyYouTubeVideo,
  getCompanies,
  Company,
  FactCheckResult,
} from "@/services/api";

export default function Analyze() {
  const navigate = useNavigate();
  
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [companyId, setCompanyId] = useState<string>("");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(true);
  const [currentStep, setCurrentStep] = useState<AnalysisStep>('extracting-transcript');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const isValid = isValidYouTubeUrl(youtubeUrl) && companyId !== "";

  // Load companies on mount
  useEffect(() => {
    const loadCompanies = async () => {
      setIsLoadingCompanies(true);
      try {
        const companyList = await getCompanies();
        console.log('[Analyze] Loaded companies:', companyList);
        setCompanies(companyList);
        if (companyList.length > 0) {
          setCompanyId(companyList[0].company_id);
        }
      } catch (err) {
        console.error('Failed to load companies:', err);
        setError('Failed to load companies. Please refresh the page.');
      } finally {
        setIsLoadingCompanies(false);
      }
    };

    loadCompanies();
  }, []);

  const handleAnalyze = async () => {
    if (!isValid) return;

    setIsAnalyzing(true);
    setError(null);
    setProgress(0);

    try {
      // Use the integrated verification endpoint which handles everything
      setCurrentStep('extracting-transcript');
      setProgress(10);
      
      // The verifyYouTubeVideo function handles:
      // 1. Transcript extraction
      // 2. Claim extraction
      // 3. RAG retrieval
      // 4. Verification
      
      setCurrentStep('analyzing');
      setProgress(30);
      
      const factCheckResult = await verifyYouTubeVideo(youtubeUrl, companyId);
      
      setProgress(80);

      if (!factCheckResult.success) {
        throw new Error(factCheckResult.error || 'Failed to analyze content');
      }

      setProgress(100);
      setCurrentStep('complete');

      // Store results and navigate
      sessionStorage.setItem('factCheckResult', JSON.stringify(factCheckResult));
      sessionStorage.setItem('analysisMetadata', JSON.stringify({
        youtubeUrl,
        companyId,
        hadPdf: !!pdfFile,
      }));

      // Small delay to show completion state
      setTimeout(() => {
        navigate('/results');
      }, 500);

    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setIsAnalyzing(false);
    }
  };

  if (isAnalyzing) {
    return (
      <div className="container py-20">
        <LoadingAnalysis currentStep={currentStep} progress={progress} />
      </div>
    );
  }

  return (
    <div className="container py-12">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Analyze Financial Content</h1>
          <p className="text-muted-foreground">
            Enter a YouTube video URL and select a company to start fact-checking
          </p>
        </div>

        <Card className="relative">
          <CardHeader>
            <CardTitle>Content Input</CardTitle>
            <CardDescription>
              Provide the video you want to analyze and select the company to verify against
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6 relative">
            {/* Company Selection */}
            <div className="space-y-2">
              <Label htmlFor="company">Company *</Label>
              <Select
                value={companyId}
                onValueChange={(value) => {
                  console.log('[Analyze] Company selected:', value);
                  setCompanyId(value);
                }}
                disabled={isAnalyzing || isLoadingCompanies}
              >
                <SelectTrigger id="company" className="w-full">
                  <SelectValue placeholder={isLoadingCompanies ? "Loading companies..." : "Select a company"} />
                </SelectTrigger>
                <SelectContent className="z-[100]">
                  {companies.length === 0 && !isLoadingCompanies ? (
                    <SelectItem value="__no_companies__" disabled>
                      No companies available
                    </SelectItem>
                  ) : (
                    companies.map((company) => (
                      <SelectItem key={company.company_id} value={company.company_id}>
                        {company.name} {company.ticker && `(${company.ticker})`}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {companies.length === 0 && !isLoadingCompanies && (
                <p className="text-xs text-muted-foreground">
                  No companies available. Please upload documents for a company first.
                </p>
              )}
              {companies.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {companies.length} company{companies.length !== 1 ? 'ies' : ''} available
                </p>
              )}
            </div>

            {/* YouTube URL Input */}
            <div className="space-y-2">
              <Label htmlFor="youtube-url">YouTube Video URL *</Label>
              <YouTubeInput 
                value={youtubeUrl} 
                onChange={setYoutubeUrl} 
                disabled={isAnalyzing}
              />
            </div>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">
                  Optional
                </span>
              </div>
            </div>

            {/* PDF Uploader */}
            <div className="space-y-2">
              <Label>Reference Document (PDF)</Label>
              <PDFUploader 
                file={pdfFile} 
                onFileChange={setPdfFile} 
                disabled={isAnalyzing}
              />
              <p className="text-xs text-muted-foreground">
                Upload a reference document to supplement the verification (optional)
              </p>
            </div>

            {/* Error display */}
            {error && (
              <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <Button 
              onClick={handleAnalyze}
              disabled={!isValid || isAnalyzing || isLoadingCompanies}
              className="w-full gap-2"
              size="lg"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  Start Analysis
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>

            <p className="text-xs text-muted-foreground text-center">
              Analysis typically takes 30-60 seconds depending on video length
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
