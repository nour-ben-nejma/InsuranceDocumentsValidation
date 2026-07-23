import { useRef, useState } from "react";
import {
  FileText,
  IdCard,
  ShieldCheck,
  ClipboardList,
  ReceiptText,
  CreditCard,
  Camera,
  UploadCloud,
  CheckCircle2,
  X,
  Ban,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DOC_META, type DocKey, type DocState } from "@/lib/store";

const iconMap = {
  FileText,
  IdCard,
  ShieldCheck,
  ClipboardList,
  ReceiptText,
  CreditCard,
  Camera,
};

export function DocUploader({
  docKey,
  state = {},
  isUploading = false,
  onChange,
}: {
  docKey: DocKey;
  state?: DocState;
  isUploading?: boolean;
  /** Pass `undefined` to mark as unavailable, or a `File` to upload it. */
  onChange: (file?: File) => void;
}) {
  const meta = DOC_META[docKey];
  const Icon = iconMap[meta.icon as keyof typeof iconMap];
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const handleFile = (file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      alert("Fichier trop volumineux (max 10 Mo)");
      return;
    }
    onChange(file);
  };

  const safeState: DocState = state ?? {};
  const uploaded = !!safeState.fileName;
  const unavailable = !!safeState.unavailable;

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        const f = e.dataTransfer.files?.[0];
        if (f) handleFile(f);
      }}
      className={`relative rounded-lg border transition-colors p-5 ${
        uploaded
          ? "border-success/40 bg-success/5"
          : unavailable
            ? "border-warning/40 bg-warning/5"
            : drag
              ? "border-primary bg-primary/5"
              : "border-dashed border-border bg-card hover:border-primary/50"
      }`}
    >
      {isUploading && (
        <div className="absolute inset-0 rounded-lg bg-background/60 flex items-center justify-center z-10">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
        </div>
      )}
      <div className="flex items-start gap-4">
        <div
          className={`h-10 w-10 shrink-0 rounded-md flex items-center justify-center ${
            uploaded
              ? "bg-success/15 text-success"
              : unavailable
                ? "bg-warning/15 text-warning-foreground"
                : "bg-muted text-primary"
          }`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="font-medium text-sm">{meta.label}</div>
            {uploaded && <CheckCircle2 className="h-4 w-4 text-success" />}
          </div>

          {uploaded ? (
            <div className="mt-2 flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="text-sm truncate">{state.fileName}</div>
                <div className="text-xs text-muted-foreground">
                  {formatSize(state.fileSize ?? 0)}
                </div>
              </div>
              <button
                type="button"
                onClick={() => onChange(undefined)}
                className="text-muted-foreground hover:text-destructive p-1"
                aria-label="Supprimer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : unavailable ? (
            <div className="mt-2 flex items-center justify-between gap-2">
              <div className="text-sm text-muted-foreground italic">
                Marqué comme non disponible
              </div>
              <button
                type="button"
                onClick={() => onChange(undefined)}
                className="text-muted-foreground hover:text-foreground p-1"
                aria-label="Annuler"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <p className="text-xs text-muted-foreground mt-1">
                Glissez-déposez ou parcourez · PDF, JPG, PNG · 10 Mo max
              </p>
              <div className="mt-3 flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => inputRef.current?.click()}
                  disabled={isUploading}
                >
                  <UploadCloud className="h-3.5 w-3.5 mr-1.5" />
                  Parcourir
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="text-muted-foreground"
                  onClick={() => onChange(undefined)}
                  disabled={isUploading}
                >
                  <Ban className="h-3.5 w-3.5 mr-1.5" />
                  Non disponible
                </Button>
              </div>
            </>
          )}

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,image/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
              e.target.value = "";
            }}
          />
        </div>
      </div>
    </div>
  );
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} Mo`;
}