import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import {
  Plus,
  Search,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  FileClock,
  ArrowRight,
  ServerCrash,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { countUploaded, type Dossier } from "@/lib/store";
import { StatusBadge } from "@/components/status-badge";
import { useDossiers } from "@/hooks/use-dossiers";

export const Route = createFileRoute("/")({
  component: Dashboard,
});

function Dashboard() {
  const { data: dossiers = [], isLoading, isError } = useDossiers();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<string>("all");

  const filtered = useMemo(() => {
    return dossiers.filter((d) => {
      const match =
        !q ||
        d.numero.toLowerCase().includes(q.toLowerCase()) ||
        d.client.toLowerCase().includes(q.toLowerCase());
      const st = status === "all" || d.status === status;
      return match && st;
    });
  }, [dossiers, q, status]);

  const stats = useMemo(() => {
    return {
      total: dossiers.length,
      coherent: dossiers.filter((d) => d.status === "coherent").length,
      averifier: dossiers.filter((d) => d.status === "a_verifier").length,
      encours: dossiers.filter(
        (d) => d.status === "en_cours" || d.status === "brouillon",
      ).length,
    };
  }, [dossiers]);

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell>
        <div className="p-8 max-w-3xl mx-auto">
          <Card className="p-10 text-center">
            <ServerCrash className="h-10 w-10 text-destructive mx-auto mb-3" />
            <h2 className="text-lg font-semibold">Impossible de contacter le serveur</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Vérifiez que le backend FastAPI tourne sur{" "}
              <code className="bg-muted px-1 rounded">http://localhost:8000</code>
            </p>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="p-8 max-w-7xl mx-auto">
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Dossiers</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Vue d'ensemble des dossiers en cours de vérification.
            </p>
          </div>
          <Button asChild size="lg">
            <Link to="/nouveau">
              <Plus className="h-4 w-4 mr-1.5" />
              Nouveau dossier
            </Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total dossiers" value={stats.total} icon={<FileClock className="h-4 w-4" />} />
          <StatCard
            label="Cohérents"
            value={stats.coherent}
            tone="success"
            icon={<CheckCircle2 className="h-4 w-4" />}
          />
          <StatCard
            label="À vérifier"
            value={stats.averifier}
            tone="danger"
            icon={<AlertTriangle className="h-4 w-4" />}
          />
          <StatCard
            label="En cours"
            value={stats.encours}
            tone="muted"
            icon={<Loader2 className="h-4 w-4" />}
          />
        </div>

        <Card className="p-4 mb-4 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher un numéro de dossier ou un client…"
              className="pl-9"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-full sm:w-52">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tous les statuts</SelectItem>
              <SelectItem value="brouillon">Brouillon</SelectItem>
              <SelectItem value="en_cours">En cours d'analyse</SelectItem>
              <SelectItem value="coherent">Cohérent</SelectItem>
              <SelectItem value="a_verifier">À vérifier</SelectItem>
            </SelectContent>
          </Select>
        </Card>

        {filtered.length === 0 ? (
          <EmptyState hasAny={dossiers.length > 0} />
        ) : (
          <Card className="overflow-hidden p-0">
            <div className="grid grid-cols-12 px-5 py-3 border-b bg-muted/40 text-xs font-medium text-muted-foreground uppercase tracking-wide">
              <div className="col-span-3">Numéro</div>
              <div className="col-span-3">Client</div>
              <div className="col-span-2">Documents</div>
              <div className="col-span-2">Statut</div>
              <div className="col-span-2 text-right">Créé le</div>
            </div>
            {filtered.map((d) => (
              <DossierRow key={d.id} d={d} />
            ))}
          </Card>
        )}
      </div>
    </AppShell>
  );
}

function DossierRow({ d }: { d: Dossier }) {
  const uploaded = countUploaded(d);
  return (
    <Link
      to="/dossier/$id"
      params={{ id: d.id }}
      className="grid grid-cols-12 px-5 py-4 border-b last:border-b-0 items-center hover:bg-muted/40 transition-colors group"
    >
      <div className="col-span-3 font-medium text-sm">{d.numero}</div>
      <div className="col-span-3 text-sm text-muted-foreground">{d.client}</div>
      <div className="col-span-2">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-24 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${(uploaded / 5) * 100}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground tabular-nums">
            {uploaded}/5
          </span>
        </div>
      </div>
      <div className="col-span-2">
        <StatusBadge status={d.status} />
      </div>
      <div className="col-span-2 flex items-center justify-end gap-2 text-xs text-muted-foreground">
        {new Date(d.createdAt).toLocaleDateString("fr-FR")}
        <ArrowRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </Link>
  );
}

function StatCard({
  label,
  value,
  icon,
  tone = "default",
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  tone?: "default" | "success" | "danger" | "muted";
}) {
  const toneClass = {
    default: "text-primary bg-primary/10",
    success: "text-success bg-success/10",
    danger: "text-destructive bg-destructive/10",
    muted: "text-muted-foreground bg-muted",
  }[tone];
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wide text-muted-foreground font-medium">
          {label}
        </span>
        <span className={`h-7 w-7 rounded-md flex items-center justify-center ${toneClass}`}>
          {icon}
        </span>
      </div>
      <div className="text-3xl font-semibold tabular-nums">{value}</div>
    </Card>
  );
}

function EmptyState({ hasAny }: { hasAny: boolean }) {
  return (
    <Card className="p-12 text-center">
      <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4">
        <FileClock className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold">
        {hasAny ? "Aucun dossier ne correspond" : "Aucun dossier pour l'instant"}
      </h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
        {hasAny
          ? "Essayez d'ajuster la recherche ou le filtre de statut."
          : "Créez votre premier dossier pour commencer la vérification automatique."}
      </p>
      {!hasAny && (
        <Button asChild className="mt-6">
          <Link to="/nouveau">
            <Plus className="h-4 w-4 mr-1.5" />
            Nouveau dossier
          </Link>
        </Button>
      )}
    </Card>
  );
}
