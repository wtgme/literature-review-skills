# Literature Review Skills

AI agent skills for conducting and managing academic literature reviews.

This repo currently keeps two runnable versions:

1. Gemini CLI version (`.gemini/skills/`)
   - Uses Gemini CLI plus the Google Workspace extension for Gemini CLI for file editing and email:
     https://github.com/gemini-cli-extensions/workspace
   - Note: Gemini CLI can be unstable during peak demand.

2. OpenCode version (`.opencode/skills/`)
   - Added as an alternative implementation using OpenCode and a customized Google Workspace MCP for file editing and email:
     https://github.com/wtgme/google-workspace-mcp

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
Daily (or periodic) digest of recent high-quality AI papers from arXiv. Filters low-effort papers, scores by novelty and impact, flags papers that challenge the current consensus, groups by research theme, and emails the digest to the configured address.

```
fetch-latest-ai-papers [category-or-topic] [days-back]
```

## Structure

```
.gemini/skills/            # Version 1: Gemini CLI skills

.opencode/skills/
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

## Setup

Set the following environment variables before running the skills (e.g. in `~/.zshrc` or `~/.bashrc`):

```sh
export DIGEST_EMAIL="you@example.com"           # fetch-latest-ai-papers: digest recipient
export GDRIVE_SUMMARIES_FOLDER_ID="<folder-id>" # summarize-paper: Google Drive folder for review docs
export GDRIVE_INDEX_DOC_ID="<doc-id>"           # summarize-paper: Google Drive index document
```

The folder/doc IDs can be found in the URL when the file is open in Google Drive:
- Folder: `https://drive.google.com/drive/folders/<folder-id>`
- Doc: `https://docs.google.com/document/d/<doc-id>/edit`

## Daily Cron Job

**1. Create the env file** (never committed to git):

```sh
cat > ~/.env.literature-review <<'EOF'
export DIGEST_EMAIL="you@example.com"
export GDRIVE_SUMMARIES_FOLDER_ID="<folder-id>"
export GDRIVE_INDEX_DOC_ID="<doc-id>"
EOF
```

**2. Make the script executable:**

```sh
chmod +x scripts/run-daily-digest.sh
```

**3. Create the log directory:**

```sh
mkdir -p ~/logs
```

**4. Add the cron entry** (`crontab -e`):

```cron
# Daily AI paper digest at 8am
0 8 * * * /path/to/literature-review-skills/scripts/run-daily-digest.sh
```

Replace `/path/to/literature-review-skills` with the absolute path to this repo. Logs are written to `~/logs/literature-review-digest.log`.

## Requirements

- opencode with skills support
- Gemini CLI (optional, for the `.gemini/` version)
- Python 3 (for the shared fetch utilities)
- Google Workspace extension for Gemini CLI (Gemini version): https://github.com/gemini-cli-extensions/workspace
- Customized Google Workspace MCP (OpenCode version): https://github.com/wtgme/google-workspace-mcp
