---
name: fetch-latest-ai-papers
description: Fetch and summarise the latest high-quality AI papers from arXiv. Filters by recency and quality signals, prioritises work from high-impact labs, flags papers that challenge the current SOTA/consensus, groups by research theme, and highlights the most significant work. Use when the user wants a digest of recent AI research.
argument-hint: [optional-category-or-topic] [optional-days-back]
allowed-tools: [Read, Write, Bash, WebFetch]
---

# Latest AI Papers from arXiv

Fetch, filter, and summarise recent high-quality AI papers from arXiv. Produce a curated digest grouped by research theme, with explicit SOTA trend tracking and flagging of papers that challenge the current consensus.

## Inputs

- `$ARGUMENTS[0]` (optional): arXiv category or sub-topic. Defaults to a broad AI sweep.
  - Common values: `cs.LG` (ML), `cs.CL` (NLP), `cs.CV` (vision), `cs.AI` (general AI), `cs.RO` (robotics), `stat.ML`
  - Can also be a topic phrase like `"diffusion models"` or `"LLM agents"`
- `$ARGUMENTS[1]` (optional): How many days back to look. Default: 7.

## Workflow

### 1. Determine Search Scope

If `$ARGUMENTS[0]` is a category code (e.g. `cs.LG`), search that category.
If it is a topic phrase, search across all AI-relevant categories.
If nothing is provided, search across: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`, `cs.NE`.

### 2. Fetch and Deduplicate

Run the shared fetch utility via Bash. It handles arXiv retrieval, Semantic Scholar enrichment (citation counts), and deduplication by arXiv ID and normalised title.

For category-based or default searches:
```
python3 .gemini/skills/shared/fetch_arxiv.py recent \
  --cats cs.AI cs.LG cs.CL cs.CV cs.NE --max 150 --days <N>
```

For a single specified category (e.g. `cs.CL`):
```
python3 .gemini/skills/shared/fetch_arxiv.py recent \
  --cats cs.CL --max 150 --days <N>
```

For topic-phrase searches:
```
python3 .gemini/skills/shared/fetch_arxiv.py search "<phrase>" \
  --max 100 --days <N> --cats cs.AI cs.LG cs.CL cs.CV cs.NE
```

The utility outputs a JSON array to stdout. Each paper dict contains:
`arxiv_id`, `title`, `authors`, `year`, `pub_date`, `abstract`, `categories`, `url`, `source`,
and (from Semantic Scholar results) `citation_count`.

**Important**: The `url` field is already set to `https://arxiv.org/abs/<arxiv_id>`. Use this field directly in all output — never construct URLs manually.

Note the total paper count after deduplication — use it as "Papers screened" in the digest header.

### 3. Low-Effort Variant Pre-Filter

Before scoring, discard papers that match **2 or more** of the following patterns. Apply this to the full retrieved pool so the scoring step works on a cleaner candidate set.

**Pattern A — Application wrapper** (no architectural change):
Signal: abstract says "we apply [existing model] to [domain]" or "we fine-tune [base model] on [dataset]" with no description of a modified architecture, loss, or training procedure.
Exception: the application domain is itself novel and the paper provides a genuinely new dataset or benchmark as part of the contribution.

**Pattern B — Benchmark-only contribution** (no new method):
Signal: the paper's stated contribution is a new evaluation dataset or leaderboard for an already well-studied task.
Exception: the benchmark reveals a failure mode not visible in existing benchmarks, or enables a new training paradigm.

**Pattern C — Training recipe variation only**:
Signal: the method section describes only learning rate schedules, data mixture ratios, tokeniser choices, or batching strategies applied to an existing architecture with no other change — the claimed gain is entirely attributable to engineering, not a conceptual advance.

**Pattern D — Re-implementation with more compute**:
Signal: the paper trains an existing published architecture on more data or at larger scale, with all baseline comparisons being the original paper's numbers and no contemporaneous strong baselines compared.

**Pattern E — Survey without novel synthesis**:
Signal: the paper catalogues existing work without proposing a new taxonomy, revealing a previously unrecognised gap, or making cross-paradigm connections not explicit in prior literature.

If fewer than 30 papers survive this filter (common for narrow categories or short windows), relax to single-pattern matches: keep those papers but flag them as "low novelty" rather than excluding them.

### 4. Quality Scoring

Score each surviving paper to select the top 20–30 for the digest.

#### Base Score (0–10)

| Criterion | Score |
|-----------|-------|
| Abstract describes a specific, falsifiable claim or result | +2 |
| Method introduces an architectural or algorithmic novelty | +2 |
| Includes quantitative benchmark comparisons to contemporaneous baselines | +2 |
| Addresses an active research direction (not solved or dormant) | +2 |
| Abstract is concrete and technical (not vague or marketing-heavy) | +1 |
| Has any Semantic Scholar citation count > 0 already | +1 |

#### Lab Impact Tier Adjustment

This is a **tiebreaker for equally-scored papers, not a veto**. A well-scored paper from an unknown lab beats a mediocre Tier 1 paper.

**Tier 1 (+2)** — Consistently field-defining:
- Research labs: Google DeepMind, OpenAI, Meta FAIR, Microsoft Research, Anthropic, Apple ML Research
- Academic: MIT CSAIL, Stanford SAIL, CMU ML/LTI, UC Berkeley BAIR, University of Toronto / Vector Institute, ETH Zurich AI Center, Oxford ML Group, Cambridge

**Tier 2 (+1)** — Frequently impactful:
- Research labs: IBM Research, Amazon Science, NVIDIA Research, Salesforce Research, Adobe Research, Allen Institute for AI (AI2), Shanghai AI Lab, KAUST AI
- Academic: Princeton NLP, UMass NLP/IR, Georgia Tech, NYU, UCLA, UCSD, University of Edinburgh, EPFL, Tsinghua KEG, Peking University

**Tier 3 (+0)** — Any named institution not listed above. Not penalised.

**Unknown / no clear affiliation (−1)** — Apply cautiously; do not penalise independent researchers with a visible track record.

If a lab not on this list has published 3+ papers at NeurIPS / ICML / ICLR in the last 2 years that appear in this same pool, treat them as Tier 2.

#### Negative Adjustments

| Criterion | Score |
|-----------|-------|
| Pre-filter survivor (matched a single pattern, kept but flagged) | −2 |
| SOTA claimed on a single benchmark only, no ablation or generalisation | −1 |
| Workshop paper or position paper with no empirical results | −1 |
| Abstract framing is 3+ years behind the current state of the field | −1 |

Select papers with the highest total scores. Aim for 20–30, preserving thematic breadth — do not let one topic dominate simply because it has many mediocre papers.

### 5. SOTA Challenge Flagging

After selecting the final paper set, scan each abstract for signals that the paper contradicts, complicates, or challenges a currently held consensus view.

Apply the badge `[! CHALLENGES CONSENSUS]` to a paper if its abstract contains any of:

- A claim that a widely-used method fails in a regime previously considered its strength (fails at scale, fails on out-of-distribution inputs, etc.)
- A negative result: a recent gain does not replicate, does not transfer, or is attributable to a confound
- A simple baseline that matches or outperforms a complex recent method
- A theoretical result bounding what current approaches can achieve in principle
- A replication study reaching materially different conclusions from the original
- Explicit contrarian framing: "contrary to recent work", "we challenge the assumption that", "surprisingly, we find that", "the gains from X do not generalise to", "we show that [widely-used method] fails to"

Flagged papers are listed in the dedicated **Challenges Consensus / Surprising Findings** section of the output *and* in their relevant thematic section. The badge travels with the paper into both locations.

### 6. Thematic Grouping

Group selected papers into 4–8 research themes. Examples:
- Foundation Models & Scaling
- Reasoning & Planning
- Efficient Architectures
- Multimodal Learning
- Alignment & Safety
- Agents & Tool Use
- Diffusion & Generative Models
- Applications (healthcare, science, code, etc.)

Choose themes that fit the actual papers — do not force categories. Papers flagged `[! CHALLENGES CONSENSUS]` still belong to their most relevant theme; the badge travels with them.

### 7. Output

Print a structured digest with the sections below **in order**. Every paper entry in every section must include a clickable arXiv link using the `url` field from the paper dict. **Never omit the URL.**

---

## AI Research Digest — [Date range, e.g. Feb 16–23 2026]

**Source**: arXiv + Semantic Scholar
**Category / Topic**: [category code or topic phrase, or "Broad AI sweep"]
**Period**: last [N] days
**Papers screened**: [total after dedup] → **Selected**: [final count]

---

### Highlights

Top 3–5 papers across all themes — one sentence each with URL.

- **[Paper Title]** ([arXiv:XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX)) — [One sentence: what they did and why it matters.]
- ...

---

### SOTA Trend Tracker

For each major active area represented in the fetched batch, describe the directional movement of the current SOTA: what the leading approach was recently, what this batch's papers suggest is changing, and the direction of travel.

Only include rows with evidence from this batch — do not speculate. An empty or sparse table for a narrow topic is correct and honest.

| Research Area | Current SOTA Direction | This Week's Signal | Momentum |
|---------------|------------------------|-------------------|----------|
| [e.g. LLM Reasoning] | [e.g. Chain-of-thought + verifier models] | [e.g. 2 papers show RL-based reasoning matches CoT at 10× lower inference cost] | ↑ RL-based reasoning |
| [e.g. Efficient Attention] | [e.g. Linear attention approximations] | [e.g. Hybrid attention paper shows pure linear attention still insufficient for long-range] | → Hybrid architectures |

**Momentum symbols**: ↑ accelerating, → stable/consolidating, ↓ challenged/declining, ? contested

---

### Challenges Consensus / Surprising Findings

Papers in the selected set that contradict a current assumption, report negative results, or surface a surprising finding. Each entry includes a "What it challenges" note. These papers also appear in their relevant thematic section below.

**[Paper Title]** `[! CHALLENGES CONSENSUS]`
[Authors, shortened] | [arXiv:XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX)
**What it challenges**: [One sentence: which assumption, method, or result this paper contradicts or complicates.]
> [2–3 sentence summary: what they found, and why it is surprising given the current consensus.]

[Repeat for each flagged paper. If no papers were flagged, write: *None flagged this period.*]

---

### [Theme 1 — be specific, not generic]

**[Paper Title]** — [First Author et al.] | [arXiv:XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX)
> [2–3 sentence summary: what they did, how, and what they found. Include at least one concrete number or result if available in the abstract.]

**[Paper Title]** `[! CHALLENGES CONSENSUS]` — [First Author et al.] | [arXiv:XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX)
> [2–3 sentence summary. The badge marks papers also collected in the Challenges Consensus section above.]

---

### [Theme 2]

[Same format — continue for 4–8 themes total]

---

### Papers Worth Watching

2–4 papers that are early-stage, speculative, or harder to evaluate but potentially interesting. These are lower-scoring papers that narrowly missed the main selection but have an unusual angle worth tracking.

- **[Paper Title]** — [First Author et al.] | [arXiv:XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX)
  *Why it's interesting*: [One sentence on what makes it worth monitoring.]

---

### This Week's Trends

3–5 observational patterns across the batch — volume of work in a sub-area, community tooling emphasis, methodological shifts. This section is for observations that do not fit the SOTA Trend Tracker (which tracks directional movement). Do not repeat content from the Trend Tracker here.

- [Pattern 1]
- [Pattern 2]
- ...

---

### 8. Send Digest to Gmail

After producing the full digest output, send it to the user's Gmail using the `gmail.send` MCP tool.

**Recipient**: `$DIGEST_EMAIL`

**Subject line format**:
```
AI Research Digest — [Date range, e.g. Feb 16–23 2026]
```

**Body**: The complete digest from Step 7, converted to plain text (preserve markdown structure — headings, bullets, and URLs will render cleanly in Gmail).

Call `gmail.send` with:
- `to`: `$DIGEST_EMAIL`
- `subject`: the subject line above
- `body`: the full digest text

After sending, confirm: "Digest sent to $DIGEST_EMAIL."

---

## Notes on Curation

- Be selective — 15–25 papers is better than 50 mediocre ones
- Write summaries that go beyond paraphrasing the abstract: explain *why* the approach is interesting or what makes it technically novel
- Flag if a paper makes bold claims that seem undersubstantiated
- If a sub-area is particularly active this week, note it
- Apply the low-effort pre-filter before scoring to avoid polluting the scoring pool with papers that consume quota but add no value
- The SOTA Trend Tracker should only contain rows with evidence from this batch; an empty tracker for a narrow topic is correct and honest
- Lab Impact Tier is a tiebreaker: a well-scored paper from an unknown lab always beats a mediocre paper from Tier 1
