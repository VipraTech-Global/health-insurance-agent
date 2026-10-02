"""Inventory official register entries separately from admitted current editions.

A register entry is not a verified current retail plan. Keep scope exclusions,
withdrawals and uncertain editions visible without promoting them to evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin

from .acquisition import document_role


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    parent: Node | None = field(default=None, repr=False)

    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())

    def find(self, tag):
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    yield child
                yield from child.find(tag)


class RegisterHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Node('root')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for n in range(len(self.stack) - 1, 0, -1):
            if self.stack[n].tag == tag:
                del self.stack[n:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def scope(name: str, uin: str = '') -> tuple[str, str]:
    if re.search(r'\bclaims?\b|intimation|reimbursement|hospital network|ID Proofs|E-Card|whistle|stewardship|citizen charter|agents|grievance|GRO details|empanelment|disclosure|underwriting|product list|advisory|IRDAI circular|^others$|^services$', name, re.I):
        return 'excluded', 'Administrative/download navigation item, not a standalone retail plan.'
    if re.search(r'repric|health check|preventive', name, re.I):
        return 'reference_only', 'Supporting schedule or notice, not a standalone retail plan.'
    if re.search(r'group|travel|overseas|personal.?accident|accident (?:care|shield|armour)|saral suraksha|PMSBY', name, re.I) or 'HLGP' in uin:
        return 'excluded', 'Group, travel or personal-accident product.'
    if re.search(r'rider|add.?on|endorsement|HLIA', name + ' ' + uin, re.I):
        return 'reference_only', 'Optional cover; retain separately from base plans.'
    return 'review_pending', 'Retail scope, current edition, variants and coverage basis need confirmation.'


def register_rows(key: str, html: str, source: dict) -> list[dict]:
    parser = RegisterHTML()
    parser.feed(html)
    root = parser.root
    entries = []

    def add(label, anchors, default_role=None):
        if not label:
            return
        uin = re.search(r'\b[A-Z]{3}HL[A-Z]+\d+V\d+\b', label)
        uin = uin[0] if uin else ''
        name = re.sub(r'\s*\((?:UIN\s*:\s*)?[A-Z]{3}HL[A-Z]+\d+V\d+\)\s*', '', label).strip()
        name = re.sub(r'\s+(?:Policy Wordings?|Policy Document)\s*$', '', name, flags=re.I)
        name = re.sub(r'\s+New$', '', name)
        name = re.sub(r'\s+Download PDF$', '', name, flags=re.I)
        status, reason = scope(name, uin)
        documents = []
        for a in anchors:
            url = urljoin(source['source_url'], a.attrs.get('href', ''))
            if '.pdf' not in url.casefold():
                continue
            text = a.text() or a.attrs.get('title', '')
            role = document_role(text + ' ' + url)
            if role == 'unresolved' and default_role:
                role = default_role
            documents.append({'url': url, 'label': text, 'role': role,
                              'status': 'excluded' if role == 'excluded' else 'discovered'})
        entries.append({'insurer_id': key, 'name': name, 'name_as_listed': label, 'uin': uin,
            'scope': status, 'reason': reason, 'edition_status': 'unresolved', 'variant_status': 'unresolved',
            'source_url': source['source_url'], 'source_sha256': source['source_sha256'],
            'retrieved_at': source['retrieved_at'], 'documents': documents})

    if key == 'bajaj':
        for row in root.find('tr'):
            cells = list(row.find('td'))
            anchors = list(row.find('a'))
            if cells and len(anchors) > 1:
                add(cells[0].text(), anchors)
    elif key == 'tata':
        for heading in root.find('h3'):
            if heading.text() == 'Health Retail':
                for a in heading.parent.find('a'):
                    add(a.text(), [a])
    elif key == 'hdfc':
        for a in root.find('a'):
            label = a.text()
            if '.pdf' not in a.attrs.get('href', '').casefold() or not label:
                continue
            if re.search(r'product list|regulatory|ayush treatments|stewardship|disclosure|disclaimer|GST|policy of protection|cashless services', label, re.I):
                continue
            add(label, [a], 'base_wording')
    elif key == 'niva':
        for a in root.find('a'):
            if '/policy_wording/' in a.attrs.get('href', '').casefold():
                add(a.text(), [a], 'base_wording')
    elif key == 'newindia':
        for a in root.find('a'):
            if '/health-insurance/' in a.attrs.get('href', '') and a.text():
                add(re.sub(r'\s*\(Cashless.*', '', a.text(), flags=re.I), [])
    elif key == 'aditya':
        for a in root.find('a'):
            if a.attrs.get('data-toggle') == 'tab' and a.attrs.get('href') == 'javascript:void(0)':
                add(a.text(), [])
        for item in root.find('li'):
            if 'navtab' in item.attrs.get('class', '').split():
                add(item.text(), [])
    elif key == 'manipal':
        for a in root.find('a'):
            if '/downloads/products/-/categories/' in a.attrs.get('href', '') and a.text():
                add(a.text(), [])
    elif key == 'icici':
        for a in root.find('a'):
            if '.pdf' not in a.attrs.get('href', '').casefold():
                continue
            parent = a.parent
            while parent and parent.tag not in {'li', 'root'}:
                parent = parent.parent
            if parent and parent.tag == 'li':
                add(parent.text(), [a], 'base_wording')
    # Merge role associations without treating duplicate document links as plans.
    merged = {}
    for row in entries:
        identity = row['uin'] or row['name'].casefold()
        if identity not in merged:
            merged[identity] = row
        else:
            known = {d['url'] for d in merged[identity]['documents']}
            merged[identity]['documents'].extend(d for d in row['documents'] if d['url'] not in known)
    return sorted(merged.values(), key=lambda r: (r['name'].casefold(), r['uin']))
