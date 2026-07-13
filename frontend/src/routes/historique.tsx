import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { useDossiers } from "@/hooks/use-dossiers";
import { Loader2 } from "lucide-react";

export const Route = createFileRoute("/historique")({
  component: Historique,
});

function Historique() {
  const { data: dossiers = [], isLoading, isError } = useDossiers();

  const sortedDossiers = [...dossiers].sort((a, b) => b.createdAt - a.createdAt);

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
          <Card className="p-10 text-center text-destructive">
            Une erreur est survenue lors de la récupération de l'historique depuis la base de données.
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="p-8 max-w-5xl mx-auto">
        <h1 className="text-2xl font-semibold tracking-tight">Historique</h1>
        <p className="text-sm text-muted-foreground mt-1 mb-6">
          Journal chronologique de tous les dossiers traités.
        </p>
        <Card className="p-0 overflow-hidden">
          {sortedDossiers.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Aucun dossier dans l'historique.
            </div>
          ) : (
            sortedDossiers.map((d) => (
              <Link
                key={d.id}
                to="/dossier/$id"
                params={{ id: d.id }}
                className="flex items-center justify-between px-5 py-4 border-b last:border-b-0 hover:bg-muted/40"
              >
                <div>
                  <div className="font-medium text-sm">{d.numero}</div>
                  <div className="text-xs text-muted-foreground">
                    {d.client} · {new Date(d.createdAt).toLocaleString("fr-FR")}
                  </div>
                </div>
                <StatusBadge status={d.status} />
              </Link>
            ))
          )}
        </Card>
      </div>
    </AppShell>
  );
}