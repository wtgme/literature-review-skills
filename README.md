# Literature Review Skills

AI agent skills for conducting and managing academic literature reviews. Built for Gemini CLI (`.gemini/skills/`) with a shared Python utility for paper retrieval.

## Skills

### `summarize-paper`
Critical peer-review-style analysis of a paper (PDF, URL, or arXiv ID). Produces a structured review covering contributions, method, relation to prior work, strengths, limitations, and future extensions. Saves the review to Google Drive and updates a searchable index doc.

```
summarize-paper <paper-path-or-url-or-arxiv-id> [github-repo-url]
```

### `domain-literature-review`
Full literature review for a research domain. Searches arXiv and Semantic Scholar, screens and ranks papers, builds a field timeline, synthesises findings thematically, and produces a structured review document with individual paper summaries.

```
domain-literature-review "<keywords>" [max-papers]
```

### `fetch-latest-ai-papers`
Weekly digest of recent high-quality AI papers from arXiv. Filters low-effort papers, scores by novelty and impact, flags papers that challenge the current consensus, groups by research theme, and emails the digest to the configured address.

```
fetch-latest-ai-papers [category-or-topic] [days-back]
```

## Structure

```
.gemini/skills/
├── summarize-paper/
│   ├── SKILL.md          # Skill definition
│   └── parse_paper.py    # Paper ingestion (arXiv, PDF, URL)
├── fetch-latest-ai-papers/
│   └── SKILL.md
├── domain-literature-review/
│   └── SKILL.md
└── shared/
    └── fetch_arxiv.py    # Shared arXiv + Semantic Scholar fetch utility

reviews/                  # Output: reviews and per-paper summaries
```

## Requirements

- [Gemini CLI](https://github.com/google-gemini/gemini-cli) with skills support
- Python 3 (for the shared fetch utilities)
- Google Drive MCP tool (for `summarize-paper` save/index features)
- Gmail MCP tool (for `fetch-latest-ai-papers` email delivery)
