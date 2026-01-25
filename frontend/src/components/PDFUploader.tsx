import { useState, useCallback, useRef } from "react";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { FileText, Upload, X, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface PDFUploaderProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
}

export function PDFUploader({ file, onFileChange, disabled }: PDFUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      onFileChange(droppedFile);
    }
  }, [disabled, onFileChange]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      onFileChange(selectedFile);
    }
  }, [onFileChange]);

  const handleRemove = useCallback(() => {
    onFileChange(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }, [onFileChange]);

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-accent" />
        Reference PDF
        <span className="text-muted-foreground text-xs font-normal">(optional)</span>
      </Label>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handleFileSelect}
        disabled={disabled}
        className="hidden"
      />

      {!file ? (
        <div
          onClick={handleClick}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
            isDragOver
              ? "border-accent bg-accent/5"
              : "border-muted-foreground/25 hover:border-accent hover:bg-muted/50",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
          <p className="text-sm font-medium mb-1">
            Drop a PDF here or click to upload
          </p>
          <p className="text-xs text-muted-foreground">
            Upload official documents to cross-reference claims
          </p>
        </div>
      ) : (
        <div className="flex items-center gap-3 p-4 border rounded-lg bg-muted/30">
          <div className="h-10 w-10 rounded bg-accent/10 flex items-center justify-center">
            <FileText className="h-5 w-5 text-accent" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </p>
          </div>
          <CheckCircle className="h-4 w-4 text-success" />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRemove}
            disabled={disabled}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Add financial reports, SEC filings, or other official documents for comparison
      </p>
    </div>
  );
}
