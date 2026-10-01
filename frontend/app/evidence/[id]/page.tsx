"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CitationViewer, type CitationView } from "../../../components/citation-viewer";
import { api } from "../../../lib/api";
import type { components } from "../../../lib/api-schema";

type Evidence = components["schemas"]["EvidenceDetail"];

export default function EvidencePage() {
  const { id } = useParams<{ id: string }>();
  const [citation, setCitation] = useState<CitationView | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<Evidence>(`/api/v2/evidence/${encodeURIComponent(id)}/`).then(evidence => {
      if (!active) return;
      setCitation({
        documentVersionId: evidence.document_version_id,
        evidenceSpanId: evidence.id,
        page: evidence.page, quote: evidence.quote,
        label: `Policy source · physical page ${evidence.page ?? "unknown"}`,
        bbox: null,
      });
    }).catch(caught => { if (active) setError(caught instanceof Error ? caught.message : "Could not open citation."); });
    return () => { active = false; };
  }, [id]);
  return <main className="workspace">
    <p>Policy source review</p>
    {error ? <p className="error">{error}</p> : citation ? <CitationViewer citation={citation} onClose={() => window.history.back()} /> : <p>Loading citation…</p>}
  </main>;
}
