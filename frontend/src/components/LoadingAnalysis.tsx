import { Progress } from "@/components/ui/progress";
import { Youtube, FileSearch, Brain, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type AnalysisStep = 
  | 'extracting-transcript'
  | 'extracting-pdf'
  | 'querying-rag'
  | 'analyzing'
  | 'complete';

interface LoadingAnalysisProps {
  currentStep: AnalysisStep;
  progress: number;
}

const steps = [
  {
    id: 'extracting-transcript',
    label: 'Extracting Transcript',
    description: 'Getting video content...',
    icon: Youtube,
  },
  {
    id: 'extracting-pdf',
    label: 'Processing Document',
    description: 'Extracting PDF content...',
    icon: FileSearch,
  },
  {
    id: 'querying-rag',
    label: 'Retrieving Documents',
    description: 'Searching official sources...',
    icon: FileSearch,
  },
  {
    id: 'analyzing',
    label: 'AI Analysis',
    description: 'Fact-checking claims...',
    icon: Brain,
  },
  {
    id: 'complete',
    label: 'Complete',
    description: 'Analysis finished!',
    icon: CheckCircle,
  },
];

export function LoadingAnalysis({ currentStep, progress }: LoadingAnalysisProps) {
  const currentStepIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="w-full max-w-md mx-auto space-y-8 animate-fade-in">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">Analyzing Content</h2>
        <p className="text-muted-foreground">
          Please wait while we verify the claims...
        </p>
      </div>

      <Progress value={progress} className="h-2" />

      <div className="space-y-4">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = step.id === currentStep;
          const isComplete = index < currentStepIndex;
          const isPending = index > currentStepIndex;

          // Skip PDF step visually if not relevant
          if (step.id === 'extracting-pdf' && currentStep !== 'extracting-pdf' && currentStepIndex > 1) {
            return null;
          }

          return (
            <div
              key={step.id}
              className={cn(
                "flex items-center gap-4 p-3 rounded-lg transition-all",
                isActive && "bg-primary/5 border border-primary/20",
                isComplete && "opacity-60",
                isPending && "opacity-40"
              )}
            >
              <div
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center",
                  isActive && "bg-primary text-primary-foreground animate-pulse-slow",
                  isComplete && "bg-success text-success-foreground",
                  isPending && "bg-muted text-muted-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              
              <div className="flex-1">
                <p className={cn(
                  "font-medium",
                  isActive && "text-primary"
                )}>
                  {step.label}
                </p>
                <p className="text-sm text-muted-foreground">
                  {isActive ? step.description : isComplete ? 'Done' : 'Waiting...'}
                </p>
              </div>

              {isComplete && (
                <CheckCircle className="h-5 w-5 text-success" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
