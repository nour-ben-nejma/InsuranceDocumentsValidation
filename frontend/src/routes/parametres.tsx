import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/parametres")({
  component: Parametres,
});

function Parametres() {
  return (
    <AppShell>
      <div className="p-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold tracking-tight">Paramètres</h1>
        <p className="text-sm text-muted-foreground mt-1 mb-6">
          Configuration de l'agent et de la connexion à l'API de vérification.
        </p>
        <Card className="p-6 space-y-5">
          <div className="space-y-2">
            <Label>Nom de l'agent</Label>
            <Input defaultValue="Sami Trabelsi" />
          </div>
          <div className="space-y-2">
            <Label>Agence</Label>
            <Input defaultValue="Tunis Centre" />
          </div>
          <div className="space-y-2">
            <Label>Endpoint API</Label>
            <Input placeholder="https://api.insurance-dv.local" />
          </div>
          <div className="flex justify-end">
            <Button onClick={() => toast.success("Paramètres enregistrés")}>
              Enregistrer
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}