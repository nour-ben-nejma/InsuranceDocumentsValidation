import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { useStore } from "@/lib/store";

export const Route = createFileRoute("/historique")({
  component: Historique,
});

function Historique() {
  const dossiers = useStore((s) =>
    [...s.dossiers].sort((a, b) => b.createdAt - a.createdAt),
  );
  return (
    <AppShell>
      <div className="p-8 max-w-5xl mx-auto">
        <h1 className="text-2xl font-semibold tracking-tight">Historique</h1>
        <p className="text-sm text-muted-foreground mt-1 mb-6">
          Journal chronologique de tous les dossiers traités.
        </p>
        <Card className="p-0 overflow-hidden">
          {dossiers.length === 0 ? (
            <div className="p-10 text-center text-sm text-muted-foreground">
              Aucun dossier dans l'historique.
            </div>
          ) : (
            dossiers.map((d) => (
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