"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

export type CitationView = {
  documentVersionId: string | null;
  page: number | null;
  quote: string;
  label: string;
  bbox: [number, number, number, number] | null;
  evidenceSpanId?: string;
  pdfUrl?: string;
  boxes?: [number, number, number, number][];
};

function clauseBoxes(context: { notes?: unknown[] }): [number, number, number, number][] | null {
  const encoded = context.notes?.find((note): note is string => typeof note === "string" && note.startsWith("clause_rectangles:"));
  if (!encoded) return null;
  const boxes: unknown = JSON.parse(encoded.slice("clause_rectangles:".length));
  if (!Array.isArray(boxes) || !boxes.length || boxes.some(box => !Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite))) {
    throw new Error("The clause highlight coordinates are invalid.");
  }
  return boxes as [number, number, number, number][];
}

export function CitationViewer({ citation, onClose }: { citation: CitationView; onClose: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const documentVersionId = citation.documentVersionId;
    const pageNumber = citation.page;
    if (!documentVersionId || !pageNumber) return;
    let cancelled = false;
    let renderTask: { cancel: () => void; promise: Promise<void> } | undefined;
    void (async () => {
      try {
        let boxes = citation.boxes ?? (citation.bbox ? [citation.bbox] : []);
        if (citation.evidenceSpanId) {
          const evidence = await api<{ quote: string; page: number; document_version_id: string; context: { notes?: unknown[] } }>(`/api/v2/evidence/${citation.evidenceSpanId}/`);
          if (evidence.quote !== citation.quote || evidence.page !== pageNumber || evidence.document_version_id !== documentVersionId) {
            throw new Error("The citation does not match its stored source.");
          }
          boxes = clauseBoxes(evidence.context) ?? boxes;
        }
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          "pdfjs-dist/build/pdf.worker.min.mjs",
          import.meta.url,
        ).toString();
        const pdfDocument = await pdfjs.getDocument(
          citation.pdfUrl ?? `/api/v2/documents/${documentVersionId}/file/`,
        ).promise;
        const page = await pdfDocument.getPage(pageNumber);
        if (cancelled || !canvasRef.current || !overlayRef.current) return;
        const drawerWidth = canvasRef.current.closest(".source-drawer")?.clientWidth ?? 680;
        const scale = Math.min(1.35, (drawerWidth - 40) / page.getViewport({ scale: 1 }).width);
        const viewport = page.getViewport({ scale });
        const pixelRatio = window.devicePixelRatio || 1;
        const canvas = canvasRef.current;
        canvas.width = Math.floor(viewport.width * pixelRatio);
        canvas.height = Math.floor(viewport.height * pixelRatio);
        canvas.style.width = `${viewport.width}px`;
        canvas.style.height = `${viewport.height}px`;
        const context = canvas.getContext("2d");
        if (!context) throw new Error("Canvas is unavailable.");
        context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        renderTask = page.render({ canvas, canvasContext: context, viewport });
        await renderTask.promise;
        const overlay = overlayRef.current;
        overlay.style.width = `${viewport.width}px`;
        overlay.style.height = `${viewport.height}px`;
        const marks = boxes.map(box => {
          const [x0, top, x1, bottom] = box;
          const pdfHeight = Math.abs(page.view[3] - page.view[1]);
          const [left, renderedBottom, right, renderedTop] = viewport.convertToViewportRectangle([
            x0,
            pdfHeight - bottom,
            x1,
            pdfHeight - top,
          ]);
          const mark = window.document.createElement("span");
          mark.className = "citation-highlight";
          mark.style.left = `${Math.min(left, right)}px`;
          mark.style.top = `${Math.min(renderedTop, renderedBottom)}px`;
          mark.style.width = `${Math.abs(right - left)}px`;
          mark.style.height = `${Math.abs(renderedBottom - renderedTop)}px`;
          return mark;
        });
        overlay.replaceChildren(...marks);
        marks[0]?.scrollIntoView({ block: "center", inline: "nearest" });
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Could not open source");
      }
    })();
    return () => {
      cancelled = true;
      renderTask?.cancel();
    };
  }, [citation]);

  return (
    <aside className="source-drawer" aria-label="Citation source">
      <header>
        <div><p className="eyebrow">EXACT SOURCE</p><strong>{citation.label}</strong></div>
        <button onClick={onClose} aria-label="Close source">×</button>
      </header>
      <blockquote>{citation.quote}</blockquote>
      {!citation.documentVersionId || !citation.page ? (
        <p className="source-note">This evidence is not a public policy PDF page.</p>
      ) : error ? (
        <p className="error">{error}</p>
      ) : (
        <div className="pdf-page">
          <canvas ref={canvasRef} />
          <div ref={overlayRef} className="citation-overlay" />
        </div>
      )}
    </aside>
  );
}
