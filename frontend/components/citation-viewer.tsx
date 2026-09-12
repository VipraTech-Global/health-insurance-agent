"use client";

import { useEffect, useRef, useState } from "react";

type Citation = {
  documentId: string;
  page: number;
  quote: string;
  label: string;
  rectangles: [number, number, number, number][];
};

export function CitationViewer({
  citation,
  onClose,
}: {
  citation: Citation;
  onClose: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let renderTask: { cancel: () => void; promise: Promise<void> } | undefined;
    void (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          "pdfjs-dist/build/pdf.worker.min.mjs",
          import.meta.url,
        ).toString();
        const pdfDocument = await pdfjs.getDocument(
          `/api/v1/documents/${citation.documentId}/file/`,
        ).promise;
        const page = await pdfDocument.getPage(citation.page);
        if (cancelled || !canvasRef.current || !overlayRef.current) return;
        const viewport = page.getViewport({ scale: 1.35 });
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
        overlay.replaceChildren(
          ...citation.rectangles.map((rectangle) => {
            const [left, top, right, bottom] =
              viewport.convertToViewportRectangle(rectangle);
            const mark = window.document.createElement("span");
            mark.className = "citation-highlight";
            mark.style.left = `${Math.min(left, right)}px`;
            mark.style.top = `${Math.min(top, bottom)}px`;
            mark.style.width = `${Math.abs(right - left)}px`;
            mark.style.height = `${Math.abs(bottom - top)}px`;
            return mark;
          }),
        );
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not open source");
        }
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
        <div><p className="eyebrow">SOURCE</p><strong>{citation.label}</strong></div>
        <button onClick={onClose} aria-label="Close source">×</button>
      </header>
      <blockquote>{citation.quote}</blockquote>
      {error ? <p className="error">{error}</p> : <div className="pdf-page">
        <canvas ref={canvasRef} />
        <div ref={overlayRef} className="citation-overlay" />
      </div>}
    </aside>
  );
}
