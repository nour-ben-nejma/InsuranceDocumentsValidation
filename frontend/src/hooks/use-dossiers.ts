import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Dossier, DocKey } from "@/lib/store";

const API_URL = "http://localhost:8000/dossiers";

export function useDossiers() {
  return useQuery({
    queryKey: ["dossiers"],
    queryFn: async (): Promise<Dossier[]> => {
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error("Failed to fetch dossiers");
      return res.json();
    },
  });
}

export function useDossier(id: string) {
  return useQuery({
    queryKey: ["dossier", id],
    queryFn: async (): Promise<Dossier> => {
      const res = await fetch(`${API_URL}/${id}`);
      if (!res.ok) throw new Error("Failed to fetch dossier");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useCreateDossier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ numero, client }: { numero: string; client: string }) => {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ numero, client }),
      });
      if (!res.ok) throw new Error("Failed to create dossier");
      return res.json() as Promise<Dossier>;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dossiers"] });
    },
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      docKey,
      file,
    }: {
      id: string;
      docKey: DocKey;
      file?: File;
    }) => {
      if (!file) {
        const res = await fetch(`${API_URL}/${id}/documents/${docKey}/unavailable`, {
          method: "POST",
        });
        if (!res.ok) throw new Error("Failed to mark unavailable");
        return res.json();
      }

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_URL}/${id}/documents/${docKey}`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Failed to upload document");
      return res.json() as Promise<Dossier>;
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["dossiers"] });
      qc.invalidateQueries({ queryKey: ["dossier", variables.id] });
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, docKey }: { id: string; docKey: DocKey }) => {
      const res = await fetch(`${API_URL}/${id}/documents/${docKey}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete document");
      return res.json() as Promise<Dossier>;
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["dossiers"] });
      qc.invalidateQueries({ queryKey: ["dossier", variables.id] });
    },
  });
}

export function useDeleteDossier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_URL}/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete dossier");
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dossiers"] });
    },
  });
}

export function useAnalyzeDossier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_URL}/${id}/analyse`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to analyze dossier");
      return res.json() as Promise<Dossier>;
    },
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["dossiers"] });
      qc.invalidateQueries({ queryKey: ["dossier", id] });
    },
  });
}

/** Sauvegarde les champs modifiés manuellement pour un document donné */
export function useSaveExtracted() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      docKey,
      fields,
    }: {
      id: string;
      docKey: string;
      fields: Record<string, string>;
    }) => {
      const res = await fetch(`${API_URL}/${id}/extracted`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_key: docKey, fields }),
      });
      if (!res.ok) throw new Error("Failed to save extracted fields");
      return res.json() as Promise<Dossier>;
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["dossier", variables.id] });
    },
  });
}

/** Relance uniquement la cohérence (sans OCR) avec les données déjà extraites */
export function useReanalyseDossier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_URL}/${id}/reanalyse`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to reanalyse dossier");
      }
      return res.json() as Promise<Dossier>;
    },
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["dossiers"] });
      qc.invalidateQueries({ queryKey: ["dossier", id] });
    },
  });
}

/** Build the URL to view a document in the browser */
export function getDocumentViewUrl(dossierId: string, docKey: DocKey): string {
  return `${API_URL}/${dossierId}/documents/${docKey}/view`;
}
