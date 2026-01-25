import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  HelpCircle 
} from "lucide-react";
import { cn } from "@/lib/utils";
import { 
  Claim, 
  VerdictType, 
  getVerdictLabel, 
  getVerdictColor, 
  getVerdictBgColor 
} from "@/services/api";

interface ClaimCardProps {
  claim: Claim;
  index: number;
}

const verdictIcons: Record<VerdictType, React.ComponentType<{ className?: string }>> = {
  true: CheckCircle,
  false: XCircle,
  partial: AlertCircle,
  unverifiable: HelpCircle,
};

export function ClaimCard({ claim, index }: ClaimCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  const VerdictIcon = verdictIcons[claim.verdict];

  return (
    <Card className={cn(
      "transition-all animate-fade-in",
      expanded && "ring-1 ring-primary/20"
    )} style={{ animationDelay: `${index * 100}ms` }}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            {/* Claim text */}
            <p className="font-medium leading-relaxed">
              "{claim.text}"
            </p>

            {/* Metadata row */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Verdict badge */}
              <Badge 
                variant="secondary"
                className={cn(
                  "flex items-center gap-1",
                  getVerdictBgColor(claim.verdict),
                  getVerdictColor(claim.verdict)
                )}
              >
                <VerdictIcon className="h-3 w-3" />
                {getVerdictLabel(claim.verdict)}
              </Badge>

              {/* Confidence */}
              <Badge variant="outline" className="text-xs">
                {claim.confidence}% confidence
              </Badge>

              {/* Timestamp */}
              {claim.timestamp && (
                <Badge variant="outline" className="text-xs flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {claim.timestamp}
                </Badge>
              )}
            </div>
          </div>

          {/* Expand button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="shrink-0"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 space-y-4 animate-fade-in">
          {/* Explanation */}
          <div>
            <h4 className="text-sm font-medium mb-2">Explanation</h4>
            <p className="text-sm text-muted-foreground">
              {claim.explanation}
            </p>
          </div>

          {/* Evidence */}
          {claim.evidence.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Evidence</h4>
              <div className="space-y-2">
                {claim.evidence.map((evidence, i) => (
                  <div 
                    key={i}
                    className={cn(
                      "p-3 rounded-md border-l-2 text-sm",
                      evidence.supportLevel === 'supports' && "bg-success/5 border-success",
                      evidence.supportLevel === 'contradicts' && "bg-destructive/5 border-destructive",
                      evidence.supportLevel === 'neutral' && "bg-muted border-muted-foreground"
                    )}
                  >
                    <p className="font-medium text-xs text-muted-foreground mb-1">
                      {evidence.source}
                    </p>
                    <p className="text-foreground">
                      "{evidence.excerpt}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {claim.evidence.length === 0 && (
            <p className="text-sm text-muted-foreground italic">
              No supporting documents found for this claim.
            </p>
          )}
        </CardContent>
      )}
    </Card>
  );
}
