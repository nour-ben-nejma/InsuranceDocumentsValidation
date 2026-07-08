import { create } from "zustand";
import { persist } from "zustand/middleware";

export type DocKey =
  | "carte_grise"
  | "cin"
  | "attestation"
  | "constat"
  | "facture";

export const DOC_META: Record<DocKey, { label: string; icon: string }> = {
  carte_grise: { label: "Carte grise", icon: "FileText" },
  cin: { label: "CIN", icon: "IdCard" },
  attestation: { label: "Attestation d'assurance", icon: "ShieldCheck" },
  constat: { label: "Constat amiable", icon: "ClipboardList" },
  facture: { label: "Facture de réparation", icon: "ReceiptText" },
};

export type DocState = {
  fileName?: string;
  fileSize?: number;
  uploadedAt?: number;
  unavailable?: boolean;
};

export type ExtractedFields = {
  nom?: string;
  prenom?: string;
  cin?: string;
  immatriculation?: string;
  compagnie?: string;
  dateDebut?: string;
  dateFin?: string;
  dateSinistre?: string;
  montant?: string;
  dommages?: string[];
  postes?: { libelle: string; montant: number; zone?: string }[];
};

export type Anomaly = {
  severity: "mineure" | "majeure";
  message: string;
};

export type Report = {
  global: "coherent" | "a_verifier";
  extracted: Partial<Record<DocKey, ExtractedFields>>;
  comparisons: {
    field: string;
    label: string;
    docs: DocKey[];
    values: Record<string, string | undefined>;
    ok: boolean;
  }[];
  damageMapping: {
    zone: string;
    declared: boolean;
    invoiced: boolean;
    montant?: number;
    ok: boolean;
  }[];
  anomalies: Anomaly[];
};

export type Dossier = {
  id: string;
  numero: string;
  client: string;
  createdAt: number;
  status: "brouillon" | "en_cours" | "coherent" | "a_verifier";
  docs: Record<DocKey, DocState>;
  report?: Report;
};

type Store = {
  dossiers: Dossier[];
  createDossier: (numero: string, client: string) => string;
  updateDoc: (id: string, key: DocKey, state: DocState) => void;
  setStatus: (id: string, status: Dossier["status"]) => void;
  setReport: (id: string, report: Report) => void;
  remove: (id: string) => void;
  get: (id: string) => Dossier | undefined;
};

const emptyDocs = (): Record<DocKey, DocState> => ({
  carte_grise: {},
  cin: {},
  attestation: {},
  constat: {},
  facture: {},
});

export const useStore = create<Store>()(
  persist(
    (set, get) => ({
      dossiers: [],
      createDossier: (numero, client) => {
        const id = crypto.randomUUID();
        const d: Dossier = {
          id,
          numero,
          client,
          createdAt: Date.now(),
          status: "brouillon",
          docs: emptyDocs(),
        };
        set({ dossiers: [d, ...get().dossiers] });
        return id;
      },
      updateDoc: (id, key, state) =>
        set({
          dossiers: get().dossiers.map((d) =>
            d.id === id ? { ...d, docs: { ...d.docs, [key]: state } } : d,
          ),
        }),
      setStatus: (id, status) =>
        set({
          dossiers: get().dossiers.map((d) =>
            d.id === id ? { ...d, status } : d,
          ),
        }),
      setReport: (id, report) =>
        set({
          dossiers: get().dossiers.map((d) =>
            d.id === id
              ? { ...d, report, status: report.global === "coherent" ? "coherent" : "a_verifier" }
              : d,
          ),
        }),
      remove: (id) =>
        set({ dossiers: get().dossiers.filter((d) => d.id !== id) }),
      get: (id) => get().dossiers.find((d) => d.id === id),
    }),
    { name: "idv-store" },
  ),
);

export function countUploaded(d: Dossier) {
  return Object.values(d.docs).filter((s) => s.fileName || s.unavailable).length;
}

// Deterministic mock report so the demo feels real without a backend.
export function generateMockReport(d: Dossier): Report {
  const seed = d.numero + d.client;
  const hash = [...seed].reduce((a, c) => a + c.charCodeAt(0), 0);
  const glitch = hash % 3 !== 0; // some divergences

  const nom = d.client.split(" ").slice(-1)[0] || "BENALI";
  const prenom = d.client.split(" ").slice(0, -1).join(" ") || "Mohamed";
  const cin = String(10000000 + (hash % 89999999)).padStart(8, "0");
  const immat = `${100 + (hash % 899)} TU ${1000 + (hash % 8999)}`;
  const compagnie = "STAR Assurances";

  const extracted: Report["extracted"] = {
    carte_grise: { nom, prenom, immatriculation: immat },
    cin: { nom, prenom, cin },
    attestation: {
      nom,
      prenom,
      immatriculation: immat,
      compagnie,
      dateDebut: "2025-01-15",
      dateFin: "2026-01-15",
    },
    constat: {
      immatriculation: glitch ? immat.replace(/\d$/, "9") : immat,
      dateSinistre: "2025-11-03",
      dommages: ["Aile avant droite", "Phare droit", "Pare-choc avant"],
    },
    facture: {
      montant: "1 840,000 TND",
      postes: [
        { libelle: "Remplacement aile AVD", montant: 620, zone: "Aile avant droite" },
        { libelle: "Phare AVD", montant: 480, zone: "Phare droit" },
        { libelle: "Pare-choc AV", montant: 540, zone: "Pare-choc avant" },
        ...(glitch
          ? [{ libelle: "Rétroviseur gauche", montant: 200, zone: "Rétroviseur gauche" }]
          : []),
      ],
    },
  };

  const comparisons: Report["comparisons"] = [
    {
      field: "nom",
      label: "Nom du titulaire",
      docs: ["cin", "carte_grise", "attestation"],
      values: { cin: nom, carte_grise: nom, attestation: nom },
      ok: true,
    },
    {
      field: "prenom",
      label: "Prénom",
      docs: ["cin", "carte_grise", "attestation"],
      values: { cin: prenom, carte_grise: prenom, attestation: prenom },
      ok: true,
    },
    {
      field: "immat",
      label: "N° d'immatriculation",
      docs: ["carte_grise", "attestation", "constat"],
      values: {
        carte_grise: immat,
        attestation: immat,
        constat: extracted.constat?.immatriculation,
      },
      ok: !glitch,
    },
    {
      field: "validite",
      label: "Validité assurance au sinistre",
      docs: ["attestation", "constat"],
      values: {
        attestation: "15/01/2025 → 15/01/2026",
        constat: "03/11/2025",
      },
      ok: true,
    },
  ];

  const declared = extracted.constat?.dommages ?? [];
  const invoicedZones = (extracted.facture?.postes ?? []).map((p) => p.zone);
  const zones = Array.from(new Set([...declared, ...invoicedZones])) as string[];
  const damageMapping = zones.map((zone) => {
    const isDeclared = declared.includes(zone);
    const poste = extracted.facture?.postes?.find((p) => p.zone === zone);
    return {
      zone,
      declared: isDeclared,
      invoiced: !!poste,
      montant: poste?.montant,
      ok: isDeclared && !!poste,
    };
  });

  const anomalies: Anomaly[] = [];
  if (glitch) {
    anomalies.push({
      severity: "majeure",
      message: "N° d'immatriculation du constat diffère de la carte grise.",
    });
    anomalies.push({
      severity: "majeure",
      message: "Poste facturé « Rétroviseur gauche » non déclaré dans le constat.",
    });
  }

  return {
    global: anomalies.length === 0 ? "coherent" : "a_verifier",
    extracted,
    comparisons,
    damageMapping,
    anomalies,
  };
}