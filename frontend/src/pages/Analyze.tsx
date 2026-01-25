import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { YouTubeInput } from "@/components/YouTubeInput";
import { PDFUploader } from "@/components/PDFUploader";
import { LoadingAnalysis, AnalysisStep } from "@/components/LoadingAnalysis";
import { ArrowRight, Loader2 } from "lucide-react";
import { 
  isValidYouTubeUrl, 
  extractTranscript, 
  extractPdfContent, 
  queryRAG, 
  factCheck,
  FactCheckResult,
} from "@/services/api";

export default function Analyze() {
  const navigate = useNavigate();
  
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState<AnalysisStep>('extracting-transcript');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const isValid = isValidYouTubeUrl(youtubeUrl);

  const handleAnalyze = async () => {
    if (!isValid) return;

    setIsAnalyzing(true);
    setError(null);
    setProgress(0);

    try {
      // Step 1: Extract transcript
      setCurrentStep('extracting-transcript');
      setProgress(10);
      const transcriptResult = await extractTranscript(youtubeUrl);
      
      if (!transcriptResult.success) {
        throw new Error(transcriptResult.error || 'Failed to extract transcript');
      }
      setProgress(25);

      // Step 2: Extract PDF (if provided)
      let pdfContent: string | undefined;
      if (pdfFile) {
        setCurrentStep('extracting-pdf');
        setProgress(35);
        const pdfResult = await extractPdfContent(pdfFile);
        
        if (pdfResult.success) {
          pdfContent = pdfResult.content;
        }
        setProgress(45);
      }

      // Step 3: Query RAG
      setCurrentStep('querying-rag');
      setProgress(55);
      const ragResult = await queryRAG(transcriptResult.transcript);
      setProgress(70);

      // Step 4: Run fact-check analysis
      setCurrentStep('analyzing');
      setProgress(80);
      const factCheckResult = await factCheck(
        transcriptResult.transcript,
        ragResult,
        pdfContent
      );

      if (!factCheckResult.success) {
        throw new Error(factCheckResult.error || 'Failed to analyze content');
      }

      setProgress(100);
      setCurrentStep('complete');

      // Store results and navigate
      // In a real app, you might use a state management solution or URL params
      sessionStorage.setItem('factCheckResult', JSON.stringify(factCheckResult));
      sessionStorage.setItem('analysisMetadata', JSON.stringify({
        youtubeUrl,
        videoTitle: transcriptResult.videoTitle,
        channelName: transcriptResult.channelName,
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
            Enter a YouTube video URL to start fact-checking
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Content Input</CardTitle>
            <CardDescription>
              Provide the video you want to analyze and optionally upload reference documents
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* YouTube URL Input */}
            <YouTubeInput 
              value={youtubeUrl} 
              onChange={setYoutubeUrl} 
              disabled={isAnalyzing}
            />

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
            <PDFUploader 
              file={pdfFile} 
              onFileChange={setPdfFile} 
              disabled={isAnalyzing}
            />

            {/* Error display */}
            {error && (
              <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <Button 
              onClick={handleAnalyze}
              disabled={!isValid || isAnalyzing}
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
