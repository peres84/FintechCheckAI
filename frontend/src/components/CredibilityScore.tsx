import { cn } from "@/lib/utils";

interface CredibilityScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

export function CredibilityScore({ score, size = 'md' }: CredibilityScoreProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-success';
    if (score >= 60) return 'text-accent';
    if (score >= 40) return 'text-warning';
    return 'text-destructive';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Highly Credible';
    if (score >= 60) return 'Mostly Credible';
    if (score >= 40) return 'Mixed Credibility';
    return 'Low Credibility';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'from-success/20 to-success/5';
    if (score >= 60) return 'from-accent/20 to-accent/5';
    if (score >= 40) return 'from-warning/20 to-warning/5';
    return 'from-destructive/20 to-destructive/5';
  };

  const sizeClasses = {
    sm: {
      container: 'h-20 w-20',
      score: 'text-2xl',
      label: 'text-xs',
    },
    md: {
      container: 'h-32 w-32',
      score: 'text-4xl',
      label: 'text-sm',
    },
    lg: {
      container: 'h-40 w-40',
      score: 'text-5xl',
      label: 'text-base',
    },
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className={cn(
        "relative flex items-center justify-center",
        sizeClasses[size].container
      )}>
        {/* Background circle */}
        <svg className="absolute inset-0 w-full h-full -rotate-90">
          <circle
            cx="50%"
            cy="50%"
            r="45%"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-muted"
          />
          <circle
            cx="50%"
            cy="50%"
            r="45%"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeLinecap="round"
            className={getScoreColor(score)}
            style={{
              strokeDasharray: circumference,
              strokeDashoffset: strokeDashoffset,
              transition: 'stroke-dashoffset 1s ease-out',
            }}
          />
        </svg>

        {/* Score number */}
        <div className={cn(
          "flex flex-col items-center justify-center rounded-full bg-gradient-to-b",
          getScoreBg(score),
          size === 'sm' ? 'h-16 w-16' : size === 'md' ? 'h-24 w-24' : 'h-32 w-32'
        )}>
          <span className={cn(
            "font-bold",
            getScoreColor(score),
            sizeClasses[size].score
          )}>
            {score}
          </span>
          {size !== 'sm' && (
            <span className="text-xs text-muted-foreground">/ 100</span>
          )}
        </div>
      </div>

      <p className={cn(
        "font-medium",
        getScoreColor(score),
        sizeClasses[size].label
      )}>
        {getScoreLabel(score)}
      </p>
    </div>
  );
}
