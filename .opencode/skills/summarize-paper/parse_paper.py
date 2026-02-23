#!/usr/bin/env python3
"""
parse_paper.py — Download and extract text from a paper (PDF or arXiv HTML).

Usage:
    python parse_paper.py <arxiv-id-or-url-or-local-path> [--out output.txt]

Output:
    Plain text of the paper written to --out (default: stdout)
    A JSON metadata block at the top:
        ---META---
        {"title": "...", "authors": [...], "year": "...", "arxiv_id": "...", "abstract": "..."}
        ---TEXT---
        <full paper text>
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.parse
import tempfile

def is_arxiv_id(s):
    return bool(re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', s.strip()))

def extract_arxiv_id(s):
    m = re.search(r'(\d{4}\.\d{4,5}(?:v\d+)?)', s)
    return m.group(1) if m else None

def fetch_arxiv_metadata(arxiv_id):
    """Fetch paper metadata from arXiv API (title, authors, abstract, year)."""
    clean_id = re.sub(r'v\d+$', '', arxiv_id)
    url = f"https://export.arxiv.org/api/query?id_list={clean_id}&max_results=1"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            xml = resp.read().decode('utf-8')
    except Exception as e:
        return {"arxiv_id": arxiv_id, "error": str(e)}

    # Parse with xml.etree (no deps)
    import xml.etree.ElementTree as ET
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom',
    }
    try:
        root = ET.fromstring(xml)
        entry = root.find('atom:entry', ns)
        if entry is None:
            return {"arxiv_id": arxiv_id}
        title = (entry.findtext('atom:title', '', ns) or '').strip().replace('\n', ' ')
        abstract = (entry.findtext('atom:summary', '', ns) or '').strip().replace('\n', ' ')
        authors = [a.findtext('atom:name', '', ns).strip()
                   for a in entry.findall('atom:author', ns)]
        published = entry.findtext('atom:published', '', ns)
        year = published[:4] if published else ''
        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "year": year,
            "abstract": abstract,
        }
    except Exception as e:
        return {"arxiv_id": arxiv_id, "error": str(e)}

def fetch_arxiv_html(arxiv_id):
    """Try to get full paper text from arXiv HTML endpoint."""
    clean_id = re.sub(r'v\d+$', '', arxiv_id)
    url = f"https://arxiv.org/html/{clean_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        # Check for "No HTML" message
        if 'No HTML' in html or 'not available' in html[:500]:
            return None
        return html_to_text(html)
    except Exception:
        return None

def html_to_text(html):
    """Strip HTML tags and return clean text. Uses lxml/bs4 if available, else regex."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'aside', 'figure', 'figcaption']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        # Collapse excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    except ImportError:
        # Fallback: crude regex strip
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'&\w+;', ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text

def download_pdf(url, dest_path):
    """Download a file from URL to dest_path."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(dest_path, 'wb') as f:
            f.write(resp.read())

def pdf_to_text(pdf_path):
    """Extract text from PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        parts = []
        for page in doc:
            parts.append(page.get_text("text"))
        text = '\n'.join(parts)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    except ImportError:
        raise RuntimeError(
            "PyMuPDF not installed. Run: pip install pymupdf"
        )
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")

def process_arxiv(arxiv_id):
    """Return (metadata_dict, full_text) for an arXiv paper."""
    meta = fetch_arxiv_metadata(arxiv_id)

    # Try HTML first (no PDF download needed, faster, cleaner)
    text = fetch_arxiv_html(arxiv_id)
    if text:
        meta['_source'] = 'arxiv-html'
        return meta, text

    # Fall back to PDF
    clean_id = re.sub(r'v\d+$', '', arxiv_id)
    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        download_pdf(pdf_url, tmp_path)
        text = pdf_to_text(tmp_path)
        meta['_source'] = 'arxiv-pdf'
        return meta, text
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def process_local_pdf(path):
    text = pdf_to_text(path)
    meta = {
        "title": os.path.basename(path),
        "authors": [],
        "year": "",
        "abstract": "",
        "_source": "local-pdf",
    }
    return meta, text

def process_url(url):
    """Download URL: if PDF, parse with pymupdf; else treat as HTML."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        content_type = resp.headers.get('Content-Type', '')
        data = resp.read()

    if 'pdf' in content_type or url.lower().endswith('.pdf'):
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            text = pdf_to_text(tmp_path)
        finally:
            os.unlink(tmp_path)
        meta = {"title": url.split('/')[-1], "authors": [], "year": "",
                "abstract": "", "_source": "url-pdf"}
    else:
        text = html_to_text(data.decode('utf-8', errors='replace'))
        meta = {"title": url, "authors": [], "year": "",
                "abstract": "", "_source": "url-html"}
    return meta, text

def main():
    parser = argparse.ArgumentParser(description='Extract paper text for LLM consumption.')
    parser.add_argument('input', help='arXiv ID, arXiv URL, local PDF path, or any URL')
    parser.add_argument('--out', default='-', help='Output file (default: stdout)')
    parser.add_argument('--meta-only', action='store_true',
                        help='Only output metadata JSON, skip full text')
    args = parser.parse_args()

    inp = args.input.strip()

    # Route to appropriate handler
    arxiv_id = extract_arxiv_id(inp) if ('arxiv.org' in inp or is_arxiv_id(inp)) else None

    if arxiv_id:
        meta, text = process_arxiv(arxiv_id)
    elif os.path.isfile(inp) and inp.lower().endswith('.pdf'):
        meta, text = process_local_pdf(inp)
    elif inp.startswith('http://') or inp.startswith('https://'):
        meta, text = process_url(inp)
    else:
        print(f"Error: cannot determine input type for: {inp}", file=sys.stderr)
        sys.exit(1)

    # Build output
    out_lines = []
    out_lines.append('---META---')
    out_lines.append(json.dumps(meta, ensure_ascii=False, indent=2))
    if not args.meta_only:
        out_lines.append('---TEXT---')
        out_lines.append(text)

    output = '\n'.join(out_lines)

    if args.out == '-':
        sys.stdout.write(output)
    else:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Written to {args.out}", file=sys.stderr)

if __name__ == '__main__':
    main()
