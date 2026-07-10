import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Loader2, ArrowLeft } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useCreateDossier } from "@/hooks/use-dossiers";

export const Route = createFileRoute("/nouveau")({
  component: NouveauDossier,
});

function NouveauDossier() {
  const navigate = useNavigate();
  const createMutation = useCreateDossier();
  const [numero, setNumero] = useState("");
  const [client, setClient] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!numero.trim() || !client.trim()) {
      toast.error("Veuillez renseigner le numéro de dossier et le nom du client.");
      return;
    }
    try {
      const dossier = await createMutation.mutateAsync({ numero: numero.trim(), client: client.trim() });
      toast.success("Dossier créé");
      navigate({ to: "/dossier/$id", params: { id: dossier.id } });
    } catch {
      toast.error("Erreur lors de la création du dossier. Le serveur est-il démarré ?");
    }
  };

  return (
    <AppShell>
      <div className="p-8 max-w-3xl mx-auto">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Retour aux dossiers
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Nouveau dossier</h1>
        <p className="text-sm text-muted-foreground mt-1 mb-8">
          Renseignez les informations de base. Vous pourrez ensuite charger les documents.
        </p>

        <Card className="p-6">
          <form onSubmit={submit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="numero">Numéro de dossier</Label>
              <Input
                id="numero"
                placeholder="Ex: DOS-2025-00842"
                value={numero}
                onChange={(e) => setNumero(e.target.value)}
                maxLength={40}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="client">Nom du client</Label>
              <Input
                id="client"
                placeholder="Ex: Mohamed Ben Ali"
                value={client}
                onChange={(e) => setClient(e.target.value)}
                maxLength={80}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" asChild type="button">
                <Link to="/">Annuler</Link>
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />}
                Créer le dossier
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </AppShell>
  );
}