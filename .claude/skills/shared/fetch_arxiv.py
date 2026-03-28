#!/usr/bin/env python3
"""
fetch_arxiv.py — Fetch paper metadata from arXiv and Semantic Scholar.

Usage:
    # Search by keyword
    python fetch_arxiv.py search "state space models time series" --max 40 --days 30

    # Fetch specific paper metadata by arXiv ID
    python fetch_arxiv.py get 2310.06825

Output: JSON array of paper objects to stdout.
"""

import sys
import re
import json
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ARXIV_API = "https://export.arxiv.org/api/query"
S2_API    = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_FIELDS = "title,authors,year,abstract,citationCount,externalIds,venue,publicationDate"

USER_AGENT = "Mozilla/5.0 (compatible; paper-fetcher/1.0)"

def _get(url, timeout=30):
    """Fetch URL text. Uses curl subprocess for reliability (avoids urllib SSL/timeout issues)."""
    import subprocess
    result = subprocess.run(
        ["curl", "-s", "-L", "--max-time", str(timeout),
         "-A", USER_AGENT, url],
        capture_output=True, timeout=timeout + 5
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.decode()[:200]}")
    return result.stdout.decode("utf-8", errors="replace")

def parse_arxiv_feed(xml_text, cutoff_date=None):
    """Parse arXiv Atom feed XML into list of paper dicts."""
    ns = {
        "atom":   "http://www.w3.org/2005/Atom",
        "arxiv":  "http://arxiv.org/schemas/atom",
        "dc":     "http://purl.org/dc/elements/1.1/",
    }
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("atom:entry", ns):
        # arXiv ID
        id_url = entry.findtext("atom:id", "", ns)
        arxiv_id = id_url.split("/abs/")[-1].strip() if "/abs/" in id_url else id_url

        published = entry.findtext("atom:published", "", ns)
        updated   = entry.findtext("atom:updated", "", ns)
        year = published[:4] if published else ""
        pub_date = published[:10] if published else ""

        # Date filter
        if cutoff_date and pub_date:
            try:
                if datetime.fromisoformat(pub_date) < cutoff_date:
                    continue
            except ValueError:
                pass

        title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
        abstract = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
        authors = [
            (a.findtext("atom:name", "", ns) or "").strip()
            for a in entry.findall("atom:author", ns)
        ]

        # Categories
        categories = [
            c.get("term", "")
            for c in entry.findall("atom:category", ns)
        ]

        papers.append({
            "arxiv_id":   arxiv_id,
            "title":      title,
            "authors":    authors,
            "year":       year,
            "pub_date":   pub_date,
            "abstract":   abstract,
            "categories": categories,
            "url":        f"https://arxiv.org/abs/{arxiv_id}",
            "source":     "arxiv",
        })
    return papers

def arxiv_search(query, max_results=60, categories=None, days_back=None):
    """Search arXiv by keyword query (and optional category list)."""
    q = urllib.parse.quote(query)
    if categories:
        cat_filter = "+OR+".join(f"cat:{c}" for c in categories)
        search_q = f"all:{q}+AND+({cat_filter})"
    else:
        search_q = f"all:{q}"

    url = (f"{ARXIV_API}?search_query={search_q}"
           f"&start=0&max_results={max_results}"
           f"&sortBy=relevance&sortOrder=descending")

    cutoff = None
    if days_back:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff = cutoff.replace(tzinfo=None)  # naive for comparison

    xml_text = _get(url)
    return parse_arxiv_feed(xml_text, cutoff_date=cutoff)

def arxiv_recent(categories, max_results=100, days_back=7):
    """Fetch recent submissions from given arXiv categories."""
    cat_filter = "+OR+".join(f"cat:{c}" for c in categories)
    url = (f"{ARXIV_API}?search_query={cat_filter}"
           f"&start=0&max_results={max_results}"
           f"&sortBy=submittedDate&sortOrder=descending")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).replace(tzinfo=None)
    xml_text = _get(url)
    return parse_arxiv_feed(xml_text, cutoff_date=cutoff)

def arxiv_get(arxiv_id):
    """Fetch metadata for a single arXiv paper by ID."""
    clean_id = re.sub(r"v\d+$", "", arxiv_id.strip())
    url = f"{ARXIV_API}?id_list={clean_id}&max_results=1"
    xml_text = _get(url)
    papers = parse_arxiv_feed(xml_text)
    return papers[0] if papers else None

def semantic_scholar_search(query, max_results=40):
    """Search Semantic Scholar for metadata (title, abstract, citations, venue)."""
    q = urllib.parse.quote(query)
    url = f"{S2_API}?query={q}&limit={max_results}&fields={S2_FIELDS}"
    try:
        raw = _get(url)
        data = json.loads(raw)
        papers = []
        for p in data.get("data", []):
            ext = p.get("externalIds", {}) or {}
            arxiv_id = ext.get("ArXiv", "")
            papers.append({
                "arxiv_id":      arxiv_id,
                "s2_id":         p.get("paperId", ""),
                "title":         p.get("title", ""),
                "authors":       [a.get("name", "") for a in (p.get("authors") or [])],
                "year":          str(p.get("year", "")),
                "pub_date":      p.get("publicationDate", ""),
                "abstract":      p.get("abstract", ""),
                "citation_count": p.get("citationCount", 0),
                "venue":         p.get("venue", ""),
                "url":           (f"https://arxiv.org/abs/{arxiv_id}"
                                  if arxiv_id else ""),
                "source":        "semantic-scholar",
            })
        return papers
    except Exception as e:
        print(f"[warn] Semantic Scholar search failed: {e}", file=sys.stderr)
        return []

def deduplicate(papers):
    """Deduplicate by arXiv ID, then by normalised title."""
    seen_ids = set()
    seen_titles = set()
    out = []
    for p in papers:
        aid = p.get("arxiv_id", "").strip()
        title_key = re.sub(r"\W+", " ", p.get("title", "").lower()).strip()
        if aid and aid in seen_ids:
            continue
        if title_key and title_key in seen_titles:
            continue
        if aid:
            seen_ids.add(aid)
        if title_key:
            seen_titles.add(title_key)
        out.append(p)
    return out

def main():
    parser = argparse.ArgumentParser(description="Fetch paper metadata from arXiv / Semantic Scholar")
    sub = parser.add_subparsers(dest="cmd")

    # search subcommand
    sp = sub.add_parser("search", help="Search by keyword")
    sp.add_argument("query")
    sp.add_argument("--max",  type=int, default=40, help="Max results per source")
    sp.add_argument("--days", type=int, default=None, help="Only papers from last N days")
    sp.add_argument("--cats", nargs="*",
                    default=["cs.AI","cs.LG","cs.CL","cs.CV","cs.NE"],
                    help="arXiv categories to restrict to")
    sp.add_argument("--no-s2", action="store_true", help="Skip Semantic Scholar")

    # recent subcommand
    rp = sub.add_parser("recent", help="Fetch recent papers from categories")
    rp.add_argument("--cats", nargs="*",
                    default=["cs.AI","cs.LG","cs.CL","cs.CV","cs.NE"])
    rp.add_argument("--max",  type=int, default=100)
    rp.add_argument("--days", type=int, default=7)

    # get subcommand
    gp = sub.add_parser("get", help="Fetch single paper by arXiv ID")
    gp.add_argument("arxiv_id")

    args = parser.parse_args()

    if args.cmd == "search":
        papers = arxiv_search(args.query, max_results=args.max,
                              categories=args.cats, days_back=args.days)
        if not args.no_s2:
            s2 = semantic_scholar_search(args.query, max_results=args.max)
            papers = deduplicate(papers + s2)
        else:
            papers = deduplicate(papers)

    elif args.cmd == "recent":
        papers = arxiv_recent(args.cats, max_results=args.max, days_back=args.days)
        papers = deduplicate(papers)

    elif args.cmd == "get":
        paper = arxiv_get(args.arxiv_id)
        papers = [paper] if paper else []

    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(papers, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
