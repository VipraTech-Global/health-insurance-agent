"""Validate browser-fetched bytes without admitting them to executable evidence."""

import base64
import hashlib
import io
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber

from .acquisition import document_role

OFFICIAL_HOSTS = {
    'aditya': {'www.adityabirlahealthinsurance.com'},
    'care': {'www.careinsurance.com', 'cms.careinsurance.com'},
    'niva': {'www.nivabupa.com', 'transactions.nivabupa.com'},
    'icici': {'www.icicilombard.com'},
    'newindia': {'www.newindia.co.in', 'newindia.co.in', 'wwwtr.newindia.co.in'},
}


def import_candidate(value: dict, root: Path) -> dict:
    row = {k: value[k] for k in ('insurer_id', 'label', 'url', 'source_url') if k in value}
    row.update(retrieved_at=datetime.now(UTC).isoformat(), acquisition='rendered_browser_fetch',
               applicability='unresolved', edition=None, uin=None)
    row['role'] = document_role(row.get('label', '') + ' ' + row.get('url', ''))
    for field in ('url', 'source_url'):
        url = urlparse(row.get(field, ''))
        if url.scheme != 'https' or url.hostname not in OFFICIAL_HOSTS.get(row.get('insurer_id'), set()):
            return {**row, 'status': 'unavailable', 'reason': 'Unverified official source host.'}
    if row['role'] == 'excluded':
        return {**row, 'status': 'excluded'}
    if shutil.disk_usage(root).free < 3 * 1024**3:
        return {**row, 'status': 'paused_disk', 'reason': 'Below 3 GB free.'}
    if value.get('status') != 200 or value.get('error'):
        return {**row, 'status': 'unavailable', 'reason': value.get('error', 'Browser request failed.'),
                'http_status': value.get('status')}
    try:
        header, encoded = value['data'].split(',', 1)
        if not header.startswith('data:') or not header.endswith(';base64'):
            raise ValueError('Expected a base64 browser response.')
        payload = base64.b64decode(encoded, validate=True)
        if not payload.startswith(b'%PDF-'):
            raise ValueError('Response is not PDF data (possibly a browser viewer wrapper).')
        with pdfplumber.open(io.BytesIO(payload)) as pdf:
            count = len(pdf.pages)
            if not count or any(p.width <= 0 or p.height <= 0 for p in pdf.pages):
                raise ValueError('Invalid physical pages.')
        sha = hashlib.sha256(payload).hexdigest()
        path = root / 'objects' / (sha + '.pdf')
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError('Content-addressed object failed its integrity check.')
        if not path.exists():
            path.write_bytes(payload)
        return {**row, 'status': 'acquired_unreviewed', 'sha256': sha, 'path': str(path),
                'physical_pages': count, 'bytes': len(payload)}
    except (ValueError, KeyError, OSError) as exc:
        return {**row, 'status': 'unavailable', 'reason': str(exc)}
