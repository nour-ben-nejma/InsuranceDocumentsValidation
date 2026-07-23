import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  ArrowLeft,
  Play,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Printer,
  RefreshCw,
  Pencil,
  ScanText,
  ShieldQuestion,
  GitCompareArrows,
  FileCheck2,
  Trash2,
  Eye,
  UploadCloud,
  Files,
  ChevronDown,
  ChevronUp,
  Camera,
  ImagePlus,
  X,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { DocUploader } from "@/components/doc-uploader";
import { StatusBadge } from "@/components/status-badge";
import {
  DOC_META,
  countUploaded,
  type DocKey,
  type Report,
  type DocState,
} from "@/lib/store";
import {
  useDossier,
  useUploadDocument,
  useAnalyzeDossier,
  useDeleteDocument,
  useDeleteDossier,
  useSaveExtracted,
  useReanalyseDossier,
  getDocumentViewUrl,
} from "@/hooks/use-dossiers";

export const Route = createFileRoute("/dossier/$id")({
  component: DossierPage,
});

function DossierPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const { data: dossier, isLoading, isError } = useDossier(id);
  const uploadMutation = useUploadDocument();
  const analyzeMutation = useAnalyzeDossier();
  const reanalyseMutation = useReanalyseDossier();
  const deleteDocMutation = useDeleteDocument();
  const deleteDossierMutation = useDeleteDossier();
  const [step, setStep] = useState(0);
  const [showDocs, setShowDocs] = useState(false);
  const replaceInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const analyzing = analyzeMutation.isPending;

  // Animate steps while analyzing
  useEffect(() => {
    if (!analyzing) { setStep(0); return; }
    setStep(0);
    const steps = 4;
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setStep(i);
      if (i >= steps) clearInterval(interval);
    }, 1200);
    return () => clearInterval(interval);
  }, [analyzing]);

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </AppShell>
    );
  }

  if (isError || !dossier) {
    return (
      <AppShell>
        <div className="p-8 max-w-3xl mx-auto">
          <Card className="p-10 text-center">
            <h2 className="text-lg font-semibold">Dossier introuvable</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Ce dossier n'existe pas ou a été supprimé.
            </p>
            <Button asChild className="mt-4">
              <Link to="/">Retour au tableau de bord</Link>
            </Button>
          </Card>
        </div>
      </AppShell>
    );
  }

  const requiredKeys: DocKey[] = ["carte_grise", "cin", "attestation", "constat", "facture", "permis"];
  const requiredUploaded = requiredKeys.filter((k) => dossier.docs[k]?.fileName || dossier.docs[k]?.unavailable).length;
  const canAnalyze = requiredUploaded === 6 && !analyzing;

  const runAnalysis = async () => {
    try {
      const updated = await analyzeMutation.mutateAsync(dossier.id);
      const report = updated.report as Report | undefined;
      toast.success(
        report?.global === "coherent"
          ? "Analyse terminée : dossier cohérent"
          : `Analyse terminée : ${report?.anomalies?.length ?? 0} anomalie(s) détectée(s)`,
      );
    } catch {
      toast.error("Erreur lors de l'analyse. Vérifiez que le serveur backend est démarré.");
    }
  };

  const handleDeleteDossier = async () => {
    if (!confirm("Supprimer définitivement ce dossier et tous ses documents ?")) return;
    try {
      await deleteDossierMutation.mutateAsync(dossier.id);
      toast.success("Dossier supprimé.");
      navigate({ to: "/" });
    } catch {
      toast.error("Erreur lors de la suppression du dossier.");
    }
  };

  const handleDeleteDoc = async (docKey: DocKey) => {
    if (!confirm(`Supprimer le document "${DOC_META[docKey].label}" ?`)) return;
    try {
      await deleteDocMutation.mutateAsync({ id: dossier.id, docKey });
      toast.success("Document supprimé.");
    } catch {
      toast.error("Erreur lors de la suppression du document.");
    }
  };

  const handleReplaceDoc = (docKey: DocKey) => {
    replaceInputRefs.current[docKey]?.click();
  };

  return (
    <AppShell>
      <div className="p-8 max-w-6xl mx-auto">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Tous les dossiers
        </Link>

        <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight">
                {dossier.numero}
              </h1>
              <StatusBadge status={dossier.status} />
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Client : <span className="font-medium text-foreground">{dossier.client}</span>{" "}
              · Créé le {new Date(dossier.createdAt).toLocaleDateString("fr-FR")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="h-1.5 w-32 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${(requiredUploaded / 6) * 100}%` }}
                />
              </div>
              <span className="tabular-nums">{requiredUploaded}/6</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/30"
              onClick={handleDeleteDossier}
              disabled={deleteDossierMutation.isPending}
            >
              {deleteDossierMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-1.5" />
              )}
              Supprimer le dossier
            </Button>
          </div>
        </div>

        {analyzing ? (
          <AnalyzingView step={step} />
        ) : dossier.report ? (
          <div className="space-y-6">
            <ReportView
              report={dossier.report as Report}
              dossierId={dossier.id}
              onRerun={runAnalysis}
              onReanalyse={() => reanalyseMutation.mutate(dossier.id, {
                onError: (e) => toast.error(e.message),
              })}
              onEdit={() => {}}
            />

            {/* Documents panel — collapsible after analysis */}
            <Card className="overflow-hidden">
              <button
                type="button"
                className="w-full flex items-center justify-between px-6 py-4 hover:bg-muted/30 transition-colors"
                onClick={() => setShowDocs((v) => !v)}
              >
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Files className="h-4 w-4 text-primary" />
                  Documents du dossier
                  <span className="ml-2 text-xs font-normal text-muted-foreground">
                    {requiredUploaded}/6 requis chargés
                  </span>
                </div>
                {showDocs ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </button>

              {showDocs && (
                <div className="px-6 pb-6 border-t pt-4">
                  <p className="text-xs text-muted-foreground mb-4">
                    Vous pouvez supprimer ou remplacer un document, puis relancer l'analyse.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {(Object.keys(DOC_META) as DocKey[])
                      .filter((k) => k !== "photos_degats")
                      .map((k) => {
                      const docState: DocState = dossier.docs[k] ?? {};
                      const hasFile = !!docState.fileName;
                      const isUnavailable = !!docState.unavailable;
                      const isDeleting =
                        deleteDocMutation.isPending &&
                        (deleteDocMutation.variables as { docKey: string })?.docKey === k;
                      const isUploading =
                        uploadMutation.isPending &&
                        uploadMutation.variables?.docKey === k;

                      return (
                        <div key={k} className="relative">
                          {/* Hidden replace input */}
                          <input
                            ref={(el) => { replaceInputRefs.current[k] = el; }}
                            type="file"
                            accept=".pdf,image/*"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                uploadMutation.mutate(
                                  { id: dossier.id, docKey: k, file },
                                  { onError: () => toast.error("Erreur lors de l'envoi du document.") }
                                );
                              }
                              e.target.value = "";
                            }}
                          />

                          <div
                            className={`rounded-lg border p-4 transition-colors ${
                              hasFile
                                ? "border-success/40 bg-success/5"
                                : isUnavailable
                                  ? "border-warning/40 bg-warning/5"
                                  : "border-dashed border-border bg-card"
                            }`}
                          >
                            {(isDeleting || isUploading) && (
                              <div className="absolute inset-0 rounded-lg bg-background/60 flex items-center justify-center z-10">
                                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                              </div>
                            )}

                            <div className="flex items-start justify-between gap-2 mb-2">
                              <span className="text-sm font-medium">{DOC_META[k].label}</span>
                              {hasFile && (
                                <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                              )}
                            </div>

                            {hasFile ? (
                              <>
                                <p className="text-xs text-muted-foreground truncate mb-3">
                                  {docState.fileName}
                                </p>
                                <div className="flex gap-2 flex-wrap">
                                  <a
                                    href={getDocumentViewUrl(dossier.id, k)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border bg-card hover:bg-muted transition-colors"
                                  >
                                    <Eye className="h-3.5 w-3.5" />
                                    Voir
                                  </a>
                                  <button
                                    type="button"
                                    onClick={() => handleReplaceDoc(k)}
                                    className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border bg-card hover:bg-muted transition-colors"
                                  >
                                    <UploadCloud className="h-3.5 w-3.5" />
                                    Remplacer
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteDoc(k)}
                                    className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border bg-card text-destructive hover:bg-destructive/10 transition-colors"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    Supprimer
                                  </button>
                                </div>
                              </>
                            ) : isUnavailable ? (
                              <p className="text-xs text-muted-foreground italic">
                                Marqué comme non disponible
                              </p>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleReplaceDoc(k)}
                                className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded border bg-card hover:bg-muted transition-colors"
                              >
                                <UploadCloud className="h-3.5 w-3.5" />
                                Charger
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* ─── Section Photos des dégâts post-analyse ─── */}
                  <div className="mt-4 border rounded-lg p-4 bg-muted/20">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Camera className="h-4 w-4 text-primary" />
                        <span className="text-sm font-medium">Photos des dégâts</span>
                        {(() => {
                          const n = Object.keys(dossier.docs).filter((k) => k.startsWith("photos_degats")).length;
                          return n > 0 ? (
                            <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">{n} photo{n > 1 ? "s" : ""}</span>
                          ) : null;
                        })()}
                      </div>
                      <label className="cursor-pointer">
                        <input
                          type="file"
                          multiple
                          accept="image/*"
                          className="hidden"
                          onChange={(e) => {
                            const files = Array.from(e.target.files || []);
                            const existingPhotoKeys = Object.keys(dossier.docs).filter((k) => k.startsWith("photos_degats"));
                            const nextIndex = existingPhotoKeys.length + 1;
                            files.forEach((file, i) => {
                              const slotKey = `photos_degats_${nextIndex + i}`;
                              uploadMutation.mutate(
                                { id: dossier.id, docKey: slotKey, file },
                                { onError: () => toast.error(`Erreur lors de l'envoi de ${file.name}.`) }
                              );
                            });
                            e.target.value = "";
                          }}
                        />
                        <span className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border bg-card hover:bg-muted transition-colors">
                          <ImagePlus className="h-3.5 w-3.5" />
                          Ajouter des photos
                        </span>
                      </label>
                    </div>
                    {(() => {
                      const photoKeys = Object.keys(dossier.docs).filter((k) => k.startsWith("photos_degats")).sort();
                      if (photoKeys.length === 0) {
                        return (
                          <p className="text-xs text-muted-foreground text-center py-3 italic">
                            Aucune photo. Ajoutez des photos puis relancez l'analyse.
                          </p>
                        );
                      }
                      return (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {photoKeys.map((k) => {
                            const photoState = dossier.docs[k] || {};
                            const isDeleting = deleteDocMutation.isPending &&
                              (deleteDocMutation.variables as { docKey: string })?.docKey === k;
                            return (
                              <div key={k} className="relative group rounded-md border overflow-hidden bg-card">
                                {isDeleting && (
                                  <div className="absolute inset-0 bg-background/70 flex items-center justify-center z-10">
                                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                  </div>
                                )}
                                <div className="flex items-center gap-2 px-3 py-2">
                                  <Camera className="h-4 w-4 text-muted-foreground shrink-0" />
                                  <span className="text-xs truncate flex-1">{photoState.fileName ?? k}</span>
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteDoc(k as DocKey)}
                                    className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive p-0.5"
                                    aria-label="Supprimer cette photo"
                                  >
                                    <X className="h-3.5 w-3.5" />
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-semibold">Documents du dossier</h2>
                  <span className="text-xs text-muted-foreground">
                    6 requis + 1 optionnel
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {(Object.keys(DOC_META) as DocKey[])
                    .filter((k) => k !== "photos_degats")
                    .map((k) => (
                      <DocUploader
                        key={k}
                        docKey={k}
                        state={dossier.docs[k] || {}}
                        isUploading={uploadMutation.isPending && uploadMutation.variables?.docKey === k}
                        onChange={(file?: File) =>
                          uploadMutation.mutate(
                            { id: dossier.id, docKey: k, file },
                            {
                              onError: () => toast.error("Erreur lors de l'envoi du document."),
                            }
                          )
                        }
                      />
                    ))}
                </div>

                {/* ─── Section Photos des dégâts (multi-upload) ─── */}
                <div className="mt-4 border rounded-lg p-4 bg-muted/20">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Camera className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Photos des dégâts</span>
                      <span className="text-xs text-muted-foreground">(optionnel · plusieurs photos acceptées)</span>
                    </div>
                    <label className="cursor-pointer">
                      <input
                        type="file"
                        multiple
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => {
                          const files = Array.from(e.target.files || []);
                          const existingPhotoKeys = Object.keys(dossier.docs).filter((k) =>
                            k.startsWith("photos_degats")
                          );
                          const nextIndex = existingPhotoKeys.length + 1;
                          files.forEach((file, i) => {
                            const slotKey = `photos_degats_${nextIndex + i}`;
                            uploadMutation.mutate(
                              { id: dossier.id, docKey: slotKey, file },
                              { onError: () => toast.error(`Erreur lors de l'envoi de ${file.name}.`) }
                            );
                          });
                          e.target.value = "";
                        }}
                      />
                      <span className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border bg-card hover:bg-muted transition-colors cursor-pointer">
                        <ImagePlus className="h-3.5 w-3.5" />
                        Ajouter des photos
                      </span>
                    </label>
                  </div>

                  {/* Galerie des photos uploadées */}
                  {(() => {
                    const photoKeys = Object.keys(dossier.docs)
                      .filter((k) => k.startsWith("photos_degats"))
                      .sort();
                    if (photoKeys.length === 0) {
                      return (
                        <p className="text-xs text-muted-foreground text-center py-4 italic">
                          Aucune photo ajoutée. L'analyse fonctionnera avec le texte du constat uniquement.
                        </p>
                      );
                    }
                    return (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {photoKeys.map((k) => {
                          const photoState = dossier.docs[k] || {};
                          const isDeleting = deleteDocMutation.isPending &&
                            (deleteDocMutation.variables as { docKey: string })?.docKey === k;
                          return (
                            <div key={k} className="relative group rounded-md border overflow-hidden bg-card">
                              {isDeleting && (
                                <div className="absolute inset-0 bg-background/70 flex items-center justify-center z-10">
                                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                </div>
                              )}
                              <div className="flex items-center gap-2 px-3 py-2">
                                <Camera className="h-4 w-4 text-muted-foreground shrink-0" />
                                <span className="text-xs truncate flex-1">{photoState.fileName ?? k}</span>
                                <button
                                  type="button"
                                  onClick={() => handleDeleteDoc(k as DocKey)}
                                  className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive p-0.5"
                                  aria-label="Supprimer cette photo"
                                >
                                  <X className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>
              </Card>
            </div>
            <div className="space-y-4">
              <Card className="p-6">
                <h3 className="text-sm font-semibold mb-2">Prêt pour l'analyse ?</h3>
                <p className="text-xs text-muted-foreground mb-4">
                  L'analyse extraira les champs de chaque document et vérifiera
                  leur cohérence entre eux.
                </p>
                <Button
                  className="w-full"
                  disabled={!canAnalyze}
                  onClick={runAnalysis}
                  size="lg"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Analyser le dossier
                </Button>
                {requiredUploaded < 6 && (
                  <p className="text-xs text-muted-foreground mt-3 flex items-start gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-warning-foreground shrink-0 mt-0.5" />
                    Chargez ou marquez comme non disponible les {6 - requiredUploaded}{" "}
                    document(s) requis restant(s).
                  </p>
                )}
              </Card>

              <Card className="p-6">
                <h3 className="text-sm font-semibold mb-3">Étapes automatiques</h3>
                <ul className="space-y-2 text-xs text-muted-foreground">
                  <li className="flex gap-2">
                    <ScanText className="h-4 w-4 text-primary shrink-0" />
                    Extraction OCR des champs clés
                  </li>
                  <li className="flex gap-2">
                    <GitCompareArrows className="h-4 w-4 text-primary shrink-0" />
                    Comparaison croisée entre documents
                  </li>
                  <li className="flex gap-2">
                    <ShieldQuestion className="h-4 w-4 text-primary shrink-0" />
                    Vérification de la validité assurance
                  </li>
                  <li className="flex gap-2">
                    <FileCheck2 className="h-4 w-4 text-primary shrink-0" />
                    Rapprochement dommages / facture
                  </li>
                </ul>
              </Card>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

const analysisSteps = [
  { label: "Extraction OCR des documents", icon: ScanText },
  { label: "Vérification de cohérence des identités", icon: GitCompareArrows },
  { label: "Validation des dates et couverture", icon: ShieldQuestion },
  { label: "Rapprochement dommages ↔ facture", icon: FileCheck2 },
];

function AnalyzingView({ step }: { step: number }) {
  return (
    <Card className="p-10">
      <div className="max-w-md mx-auto text-center mb-8">
        <div className="h-12 w-12 mx-auto rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
        <h2 className="text-lg font-semibold">Analyse en cours…</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Cela peut prendre jusqu'à une minute. Vous pouvez laisser cet écran
          ouvert.
        </p>
      </div>

      <ol className="max-w-md mx-auto space-y-1">
        {analysisSteps.map((s, i) => {
          const done = i < step;
          const active = i === step;
          const Icon = s.icon;
          return (
            <li key={i} className="flex items-center gap-3 py-2">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 transition-colors ${
                  done
                    ? "bg-success text-success-foreground"
                    : active
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {done ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : active ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Icon className="h-4 w-4" />
                )}
              </div>
              <span
                className={`text-sm ${
                  done ? "text-foreground" : active ? "text-foreground font-medium" : "text-muted-foreground"
                }`}
              >
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
    </Card>
  );
}

function ReportView({
  report,
  dossierId,
  onRerun,
  onReanalyse,
}: {
  report: Report;
  dossierId: string;
  onRerun: () => void;
  onReanalyse: () => void;
  onEdit: () => void;
}) {
  const coherent = report.global === "coherent";
  return (
    <div className="space-y-6">
      <Card
        className={`p-6 border-2 ${
          coherent
            ? "border-success/40 bg-success/5"
            : "border-destructive/40 bg-destructive/5"
        }`}
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div
              className={`h-12 w-12 rounded-full flex items-center justify-center ${
                coherent
                  ? "bg-success text-success-foreground"
                  : "bg-destructive text-destructive-foreground"
              }`}
            >
              {coherent ? (
                <CheckCircle2 className="h-6 w-6" />
              ) : (
                <AlertTriangle className="h-6 w-6" />
              )}
            </div>
            <div>
              <div className="text-lg font-semibold">
                {coherent ? "Dossier cohérent" : "Dossier à vérifier"}
              </div>
              <div className="text-sm text-muted-foreground">
                {coherent
                  ? "Tous les documents sont cohérents entre eux."
                  : `${report.anomalies.length} anomalie(s) détectée(s) — voir détails ci-dessous.`}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onReanalyse} title="Relancer uniquement la cohérence (sans refaire l'OCR)">
              <GitCompareArrows className="h-4 w-4 mr-1.5" />
              Cohérence
            </Button>
            <Button variant="outline" onClick={onRerun} title="Relancer l'analyse complète (OCR + cohérence)">
              <RefreshCw className="h-4 w-4 mr-1.5" />
              Relancer tout
            </Button>
            <Button variant="outline" onClick={() => window.print()}>
              <Printer className="h-4 w-4 mr-1.5" />
              Exporter
            </Button>
          </div>
        </div>
      </Card>

      <Tabs defaultValue="comparaison">
        <TabsList>
          <TabsTrigger value="comparaison">Comparaison des champs</TabsTrigger>
          <TabsTrigger value="dommages">Dommages vs facture</TabsTrigger>
          <TabsTrigger value="anomalies">
            Anomalies
            {report.anomalies.length > 0 && (
              <span className="ml-1.5 rounded-full bg-destructive text-destructive-foreground text-[10px] px-1.5 py-0.5">
                {report.anomalies.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="extraits">Champs extraits</TabsTrigger>
        </TabsList>

        <TabsContent value="comparaison" className="mt-4 space-y-3">
          {report.comparisons.length === 0 ? (
            <Card className="p-8 text-center text-sm text-muted-foreground">
              Aucune comparaison croisée disponible pour ce dossier.
            </Card>
          ) : (
            report.comparisons.map((c) => (
              <Card key={c.field} className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-medium text-sm">{c.label}</div>
                  {c.ok ? (
                    <span className="inline-flex items-center gap-1 text-xs text-success font-medium">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Cohérent
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs text-destructive font-medium">
                      <AlertTriangle className="h-3.5 w-3.5" /> Divergence
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {c.docs.map((d) => (
                    <div
                      key={d}
                      className={`rounded-md border p-3 ${
                        c.ok ? "border-border bg-card" : "border-destructive/30 bg-destructive/5"
                      }`}
                    >
                      <div className="text-[11px] uppercase tracking-wide text-muted-foreground font-medium">
                        {DOC_META[d].label}
                      </div>
                      <div className="text-sm font-medium mt-1 truncate">
                        {c.values[d] ?? "—"}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="dommages" className="mt-4">
          {report.damageMapping.length === 0 ? (
            <Card className="p-8 text-center text-sm text-muted-foreground">
              Aucun rapprochement dommages disponible pour ce dossier.
            </Card>
          ) : (
            <Card className="p-0 overflow-hidden">
              <div className="grid grid-cols-12 px-5 py-3 border-b bg-muted/40 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                <div className="col-span-4">Zone / poste</div>
                <div className="col-span-2 text-center">Déclaré (Constat)</div>
                <div className="col-span-2 text-center">Visuel (Photo)</div>
                <div className="col-span-2 text-center">Facturé</div>
                <div className="col-span-1 text-right">Montant</div>
                <div className="col-span-1 text-right">État</div>
              </div>
              {report.damageMapping.map((m, i) => (
                <div
                  key={i}
                  className={`grid grid-cols-12 px-5 py-3 border-b last:border-b-0 items-center text-sm ${
                    m.ok ? "" : "bg-destructive/5"
                  }`}
                >
                  <div className="col-span-4 font-medium">{m.zone}</div>
                  <div className="col-span-2 text-center">
                    {m.declared ? (
                      <CheckCircle2 className="h-4 w-4 text-success inline" />
                    ) : (
                      <span className="text-destructive text-xs">Non</span>
                    )}
                  </div>
                  <div className="col-span-2 text-center">
                    {m.visible === true ? (
                      <CheckCircle2 className="h-4 w-4 text-success inline" />
                    ) : m.visible === false ? (
                      <span className="text-destructive text-xs">Non</span>
                    ) : (
                      <span className="text-muted-foreground text-xs">—</span>
                    )}
                  </div>
                  <div className="col-span-2 text-center">
                    {m.invoiced ? (
                      <CheckCircle2 className="h-4 w-4 text-success inline" />
                    ) : (
                      <span className="text-destructive text-xs">Non</span>
                    )}
                  </div>
                  <div className="col-span-1 text-right tabular-nums text-muted-foreground text-xs">
                    {m.montant ? `${m.montant.toFixed(3)} TND` : "—"}
                  </div>
                  <div className="col-span-1 text-right">
                    {m.ok ? (
                      <span className="text-success text-xs font-medium">OK</span>
                    ) : (
                      <span className="text-destructive text-xs font-medium">!</span>
                    )}
                  </div>
                </div>
              ))}
            </Card>
          )}
        </TabsContent>

        <TabsContent value="anomalies" className="mt-4 space-y-2">
          {report.anomalies.length === 0 ? (
            <Card className="p-10 text-center">
              <CheckCircle2 className="h-8 w-8 text-success mx-auto mb-2" />
              <div className="font-medium">Aucune anomalie détectée</div>
              <div className="text-sm text-muted-foreground">
                Tous les points de contrôle sont cohérents.
              </div>
            </Card>
          ) : (
            report.anomalies.map((a, i) => (
              <Card
                key={i}
                className={`p-4 flex items-start gap-3 border-l-4 ${
                  a.severity === "majeure"
                    ? "border-l-destructive"
                    : "border-l-warning"
                }`}
              >
                <AlertTriangle
                  className={`h-5 w-5 shrink-0 mt-0.5 ${
                    a.severity === "majeure"
                      ? "text-destructive"
                      : "text-warning-foreground"
                  }`}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] uppercase font-semibold tracking-wide px-1.5 py-0.5 rounded ${
                        a.severity === "majeure"
                          ? "bg-destructive/15 text-destructive"
                          : "bg-warning/20 text-warning-foreground"
                      }`}
                    >
                      {a.severity}
                    </span>
                  </div>
                  <div className="text-sm mt-1">{a.message || (a as any).detail}</div>
                </div>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="extraits" className="mt-4 space-y-3">
          {Object.keys(report.extracted).length === 0 ? (
            <Card className="p-8 text-center text-sm text-muted-foreground">
              Aucun champ extrait disponible.
            </Card>
          ) : (
            (Object.keys(report.extracted) as DocKey[]).map((k) => (
              <ExtractedCard key={k} dossierId={dossierId} docKey={k} fields={report.extracted[k]!} />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ExtractedCard({
  dossierId,
  docKey,
  fields,
}: {
  dossierId: string;
  docKey: DocKey;
  fields: NonNullable<Report["extracted"][DocKey]>;
}) {
  const saveExtracted = useSaveExtracted();
  const [editing, setEditing] = useState<string | null>(null);
  const [values, setValues] = useState<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(fields)) {
      if (typeof v === "string") out[k] = v;
    }
    return out;
  });

  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(fields)) {
      if (typeof v === "string") out[k] = v;
    }
    setValues(out);
    setDirty(false);
  }, [fields]);

  const scalarEntries = Object.entries(fields).filter(
    ([, v]) => typeof v === "string",
  ) as [string, string][];
  const listEntries = Object.entries(fields).filter(([, v]) => Array.isArray(v)) as [
    string,
    string[],
  ][];

  const handleSave = () => {
    saveExtracted.mutate(
      { id: dossierId, docKey, fields: values },
      {
        onSuccess: () => {
          setDirty(false);
          setEditing(null);
        },
      }
    );
  };

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="font-medium text-sm">{DOC_META[docKey].label}</div>
        {dirty && (
          <Button
            size="sm"
            variant="default"
            onClick={handleSave}
            disabled={saveExtracted.isPending}
            className="h-7 text-xs"
          >
            {saveExtracted.isPending ? (
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            ) : (
              <CheckCircle2 className="h-3 w-3 mr-1" />
            )}
            Sauvegarder
          </Button>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {scalarEntries.map(([k]) => (
          <div key={k} className="flex items-center justify-between gap-2 border rounded-md px-3 py-2 bg-card">
            <div className="min-w-0 flex-1">
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">
                {k}
              </div>
              {editing === k ? (
                <Input
                  autoFocus
                  value={values[k] ?? ""}
                  onChange={(e) => {
                    setValues({ ...values, [k]: e.target.value });
                    setDirty(true);
                  }}
                  onBlur={() => setEditing(null)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") setEditing(null);
                  }}
                  className="h-7 mt-1"
                />
              ) : (
                <div className="text-sm font-medium truncate">{values[k]}</div>
              )}
            </div>
            <button
              type="button"
              onClick={() => setEditing(editing === k ? null : k)}
              className="text-muted-foreground hover:text-primary p-1"
              aria-label="Éditer"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
      {listEntries.map(([k, arr]) => (
        <div key={k} className="mt-3">
          <div className="text-[11px] uppercase tracking-wide text-muted-foreground mb-1.5">
            {k}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {arr.map((item, i) => (
              <span
                key={i}
                className="text-xs bg-muted rounded-md px-2 py-1 border"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      ))}
    </Card>
  );
}
