"""A single resident BGE-M3 CPU worker with live priority and exact section vectors."""

import hashlib
import hmac
import json
import queue
import threading
from concurrent.futures import Future
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from django.conf import settings


def local_token() -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), b"coverguide-demo-embedding-worker", hashlib.sha256
    ).hexdigest()


class Resident:
    def __init__(self):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        from .embedding_artifact import embedding_paths, qualified_embedding_status

        qualified, reason, _ = qualified_embedding_status()
        if not qualified:
            raise ValueError("BGE-M3 artifact identity/qualification failed: " + reason)
        model, _, tokenizer, _, _ = embedding_paths()
        self.np = np
        self.tokenizer = Tokenizer.from_file(str(tokenizer))
        self.tokenizer.no_truncation()
        self.tokenizer.enable_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(model), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self.names = {i.name for i in self.session.get_inputs()}
        self.jobs = queue.PriorityQueue()
        self.sequence = 0
        self.lock = threading.Lock()
        threading.Thread(target=self.run, daemon=True).start()

    def submit(self, texts, priority):
        future = Future()
        with self.lock:
            self.sequence += 1
            self.jobs.put((0 if priority == "live" else 1, self.sequence, texts, future))
        return future

    def run(self):
        while True:
            _, _, texts, future = self.jobs.get()
            if future.cancelled():
                self.jobs.task_done()
                continue
            try:
                vectors = []
                for text in texts:
                    encoded = self.tokenizer.encode_batch([text])
                    if len(encoded[0].ids) > 8192:
                        raise ValueError(
                            "BGE-M3 input exceeds 8192 tokens; no source was truncated."
                        )
                    feed = {
                        "input_ids": self.np.asarray([e.ids for e in encoded], dtype=self.np.int64),
                        "attention_mask": self.np.asarray(
                            [e.attention_mask for e in encoded], dtype=self.np.int64
                        ),
                        "token_type_ids": self.np.asarray(
                            [e.type_ids for e in encoded], dtype=self.np.int64
                        ),
                    }
                    outputs = self.session.run(
                        None, {k: v for k, v in feed.items() if k in self.names}
                    )
                    dense = outputs[0]
                    if dense.ndim == 3:
                        dense = dense[:, 0, :]
                    if dense.shape != (1, 1024):
                        raise ValueError("BGE-M3 returned the wrong vector dimensions.")
                    dense = dense / self.np.maximum(
                        self.np.linalg.norm(dense, axis=1, keepdims=True),
                        self.np.finfo(self.np.float32).eps,
                    )
                    vectors.append(dense[0].tolist())
                future.set_result(vectors)
            except Exception as exc:
                # Preserve explicit job failure; no zero vector or alternative model.
                future.set_exception(exc)
            finally:
                self.jobs.task_done()


def serve(port=8022):
    resident = Resident()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No customer questions in request logs.

        def do_GET(self):
            self.send_response(200 if self.path == "/health" else 404)
            self.end_headers()
            self.wfile.write(b'{"model":"BAAI/bge-m3","resident":true}')

        def do_POST(self):
            if self.path != "/embed" or not hmac.compare_digest(
                self.headers.get("Authorization", ""), "Bearer " + local_token()
            ):
                self.send_error(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 500_000:
                    raise ValueError("Invalid request length.")
                data = json.loads(self.rfile.read(length))
                texts = data["texts"]
                if (
                    not isinstance(texts, list)
                    or not 1 <= len(texts) <= 8
                    or any(not isinstance(t, str) for t in texts)
                ):
                    raise ValueError("Expected one to eight text strings.")
                if data["priority"] not in {"live", "background"}:
                    raise ValueError("Invalid priority.")
                result = resident.submit(texts, data["priority"]).result(timeout=175)
                body = json.dumps({"vectors": result}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (ValueError, KeyError, TimeoutError, RuntimeError):
                self.send_error(503, "Embedding unavailable; no alternate model used.")

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
