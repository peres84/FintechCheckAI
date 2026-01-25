import { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Youtube, AlertCircle, CheckCircle } from "lucide-react";
import { isValidYouTubeUrl } from "@/services/api";
import { cn } from "@/lib/utils";

interface YouTubeInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function YouTubeInput({ value, onChange, disabled }: YouTubeInputProps) {
  const [touched, setTouched] = useState(false);
  
  const isValid = isValidYouTubeUrl(value);
  const showError = touched && value && !isValid;
  const showSuccess = touched && value && isValid;

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  }, [onChange]);

  const handleBlur = useCallback(() => {
    setTouched(true);
  }, []);

  return (
    <div className="space-y-2">
      <Label htmlFor="youtube-url" className="flex items-center gap-2">
        <Youtube className="h-4 w-4 text-destructive" />
        YouTube URL
        <span className="text-destructive">*</span>
      </Label>
      
      <div className="relative">
        <Input
          id="youtube-url"
          type="url"
          placeholder="https://www.youtube.com/watch?v=..."
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          className={cn(
            "pr-10",
            showError && "border-destructive focus-visible:ring-destructive",
            showSuccess && "border-success focus-visible:ring-success"
          )}
        />
        
        {showError && (
          <AlertCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-destructive" />
        )}
        {showSuccess && (
          <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-success" />
        )}
      </div>

      {showError && (
        <p className="text-sm text-destructive flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          Please enter a valid YouTube URL
        </p>
      )}

      <p className="text-xs text-muted-foreground">
        Supports youtube.com/watch, youtu.be, and embed URLs
      </p>
    </div>
  );
}
