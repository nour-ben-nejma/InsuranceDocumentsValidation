import { CheckCircle2, AlertTriangle, Loader2, FilePlus2 } from "lucide-react";
import type { Dossier } from "@/lib/store";

const map: Record<
  Dossier["status"],
  { label: string; className: string; icon: React.ComponentType<{ className?: string }> }
> = {
  brouillon: {
    label: "Brouillon",
    className: "bg-muted text-muted-foreground border-border",
    icon: FilePlus2,
  },
  en_cours: {
    label: "En cours d'analyse",
    className: "bg-warning/15 text-warning-foreground border-warning/30",
    icon: Loader2,
  },
  coherent: {
    label: "Cohérent",
    className: "bg-success/15 text-success border-success/30",
    icon: CheckCircle2,
  },
  a_verifier: {
    label: "À vérifier",
    className: "bg-destructive/10 text-destructive border-destructive/30",
    icon: AlertTriangle,
  },
};

export function StatusBadge({
  status,
  size = "sm",
}: {
  status: Dossier["status"];
  size?: "sm" | "lg";
}) {
  const cfg = map[status];
  const Icon = cfg.icon;
  const spin = status === "en_cours" ? "animate-spin" : "";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${cfg.className} ${
        size === "lg" ? "px-3 py-1.5 text-sm" : "px-2.5 py-1 text-xs"
      }`}
    >
      <Icon className={`${size === "lg" ? "h-4 w-4" : "h-3.5 w-3.5"} ${spin}`} />
      {cfg.label}
    </span>
  );
}