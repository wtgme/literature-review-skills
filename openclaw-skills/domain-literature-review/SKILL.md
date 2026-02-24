---
name: domain-literature-review
description: 'Conduct a structured literature review for a specific research domain based on user-provided keywords. Searches arXiv and Semantic Scholar, selects high-quality papers, traces how the field evolved over time, synthesises findings thematically, and saves individual paper summaries. Use when the user wants a comprehensive survey of a topic area.'
metadata: {"openclaw":{"requires":{"bins":["python3","curl"]}}}
---

# Domain Literature Review

Conduct a rigorous, focused literature review based on user-specified keywords. Retrieve real papers, assess their quality and relevance, trace how the field evolved over time, synthesise findings thematically, and produce structured output that helps the reader understand the landscape — not just a list of papers.

## Inputs

- `$ARGUMENTS[0]`: Keywords / topic phrase (e.g. `"state space models for time series"`)
- `$ARGUMENTS[1]` (optional): Maximum number of papers to include (default: 15)

## Workflow

### 1. Search

Search the following sources for papers matching the keywords:

**arXiv** — use the API:
```
https://export.arxiv.org/api/query?search_query=all:<keywords>&start=0&max_results=40&sortBy=relevance&sortOrder=descending
```
Also search with category filters if the topic is clearly AI/ML (add `+AND+cat:cs.LG` or similar).

**Semantic Scholar** — use the public API:
```
https://api.semanticscholar.org/graph/v1/paper/search?query=<keywords>&limit=40&fields=title,authors,year,abstract,citationCount,externalIds,venue
```

Collect raw results from both sources. Deduplicate by title similarity.

### 2. Screen and Rank

For each candidate paper, score on:
- **Relevance** to the keywords (1–5)
- **Citation count** (proxy for impact; weight recent papers more leniently)
- **Venue quality** (top conferences/journals in the field score higher)
- **Recency** (papers from last 3 years preferred unless seminal)
- **Role in the field**: Is this a foundational paper, a pivotal methodological turn, or recent work? Aim for a set that represents the full arc of the field's development.

Select the top N papers (where N = `$ARGUMENTS[1]` or 15). Aim for:
- A mix of foundational / seminal papers and recent work
- Coverage of different sub-themes within the domain
- At least a few papers from the last 12 months
- Papers that represent distinct moments in the field's development, not just the highest-cited cluster

### 3. Retrieve and Read Papers

For each selected paper:
- Fetch the abstract and any available full text (arXiv HTML preferred: `https://arxiv.org/html/<id>`)
- Extract: title, authors, year, venue, DOI/arXiv ID, abstract, key methods, key results

**Additionally, for each paper, note:**
- Which earlier works it explicitly builds on or extends (check its Introduction and Related Work sections)
- Which contemporaneous works it positions itself against or compares to
- Any language about "limitations of prior work" that motivated this paper — this reveals the intellectual lineage
- Whether any of your other selected papers cite this one (building the successor map)

This relationship information is the raw material for the evolutionary narrative. Collect it before writing any synthesis.

### 4. Build a Citation Registry

Before writing any synthesis, construct a master citation registry — a private working list (not an output section) of every included paper:

```
[AuthorYear]  |  Full title  |  arXiv ID or DOI  |  Year  |  Venue
```

Every inline citation in the synthesis must use a key from this registry (e.g., `(Vaswani et al., 2017)`). No paper may be cited in the body that is not in this registry. This is your ground truth for citation accuracy.

### 5. Build a Field Timeline

Before writing any synthesis, construct an internal chronological ordering of the selected papers — a working timeline (not an output section):

- List papers in order of publication year
- Annotate each with its role: foundational framing, methodological breakthrough, empirical milestone, new direction, or incremental extension
- Note where one paper directly responds to or builds on another
- Identify 2–4 "inflection points" — moments where the field's direction materially changed

This timeline directly informs Section 3 (Historical Arc) and Section 7 (Emerging Directions) of the output.

### 6. Thematic Grouping

Identify 3–6 major themes across the selected papers. A theme is a coherent line of inquiry, not just a topic label. For each theme:
- Name the theme precisely (e.g., "Efficient Attention via Sparse and Linear Approximations", not just "Efficiency")
- Identify the **anchor paper(s)** — the work(s) that first clearly defined this theme's problem framing or proposed the approach that others followed
- Identify the current leading work within the theme
- Note which papers in other themes this theme connects to or depends on

Themes should not all be contemporaneous — some themes may have emerged earlier and fed into later ones. Capture that dependency explicitly.

### 7. Output Documents

#### A. Main Review Document

Save to `reviews/<domain-slug>/review.md`:

```markdown
# Literature Review: [Domain / Keywords]

**Date**: [today]
**Keywords**: [provided keywords]
**Papers reviewed**: [N]

---

## 1. Overview

### 1.1 Why This Field Matters
[2–3 paragraphs: the motivating problem this field addresses, why it is hard, and what success would mean. Ground this in the domain, not in the review process.]

### 1.2 Scope of This Review
[What this review covers and what it deliberately excludes. Which sub-problems and approaches are in scope. Date range and source coverage.]

---

## 2. Search Methodology

- **Sources searched**: arXiv, Semantic Scholar
- **Keywords used**: [exact queries as submitted to each API]
- **Category filters**: [if applicable]
- **Inclusion criteria**: [relevance score threshold, year range, venue tier, role in field]
- **Papers screened**: [total from both sources after deduplication] → **Papers included**: [N]
- **Notable exclusions**: [any significant papers found but excluded, and why]

---

## 3. How the Field Evolved: A Historical Arc

[This section is a chronological narrative — not a theme-by-theme breakdown. Tell the story of how the field developed over time. Use inline citations throughout.]

### 3.1 Foundations and Early Framing
[What was the state of the art before this field crystallised? What problem was the field responding to? Name the earliest key works and what they established. Approximately what years does this period cover?]

### 3.2 Pivotal Developments
[Identify 2–4 moments when the field's direction materially changed. For each: what was the prior state, what paper or result caused the shift, and what changed afterward? Use specific paper names and years. Example: "The introduction of X by Author et al. (Year) showed for the first time that Y was achievable, prompting a wave of work on Z."]

### 3.3 Emergence of Major Themes
[Explain how the major themes identified in Section 4 emerged from this history. Which themes appeared first? Did one theme enable another? Are any themes a reaction against the dominant approach of an earlier period?]

---

## 4. Thematic Synthesis

[This section is organised by intellectual theme, not by chronology. Each theme gets a structured subsection. Cite as (Author et al., Year) inline. Every citation must appear in the References section.]

### 4.1 [Theme 1 Name — be specific, not generic]

**Defining work(s)**: [Name the 1–2 papers that established this theme, in **bold**. One sentence each explaining why they are central.]

**Development of the theme**: [Narrative of how work in this theme progressed. Show the chain of reasoning: what each significant paper added, corrected, or enabled relative to what came before. Use connective language: "Building on X, Author et al. (Year) showed...", "This was challenged by...", "A key limitation of this approach — [limitation] — was addressed by..."]

**Current leading approaches**: [What are the strongest methods or results in this theme today? Name them and their key characteristics.]

**Connections to other themes**: [Does this theme share methods with another? Did it feed into a successor theme? Be explicit.]

---

### 4.2 [Theme 2 Name]

[Same structure as 4.1]

---

[Repeat for each theme, 4.3 through 4.N]

---

## 5. State of the Art

[A dedicated snapshot of where the field stands now.]

### 5.1 Leading Approaches

[Prose description of the 2–4 methods or paradigms that currently represent the frontier. For each: name it, summarise its key idea in 1–2 sentences, and note its primary strength and known limitation.]

| Approach | Representative Paper(s) | Key Strength | Key Limitation |
|----------|------------------------|--------------|----------------|
| [Method A] | (Author et al., Year) | [Strength] | [Limitation] |
| [Method B] | ... | ... | ... |

### 5.2 Settled vs. Contested

[What has the field converged on? What remains actively debated or where do competing papers reach conflicting conclusions? Name specific disagreements and the papers on each side.]

---

## 6. Research Gaps and Open Problems

[Organised by type of gap. Each bullet should name the gap specifically and, where possible, cite a paper that raised it or that demonstrates its importance. If no paper can be cited, mark it explicitly as the reviewer's inference.]

### 6.1 Theoretical Gaps
- [What is not understood formally or mathematically? What lacks a proof, a bound, or a principled explanation?]

### 6.2 Empirical Gaps
- [What has not been tested, compared, or replicated? What benchmarks are missing or inadequate?]

### 6.3 Application Gaps
- [Where do current methods fail to generalise to real-world settings, scale to production, or address practitioner needs?]

### 6.4 Community Disagreements
- [Where do papers in this review reach conflicting conclusions? What unresolved debates shape the direction of current work?]

---

## 7. Emerging Directions

[For each direction, cite the recent papers that point toward it and characterise how near-term or speculative it is.]

### 7.1 Active Frontiers
[Directions already underway, with papers from the last 12–18 months actively pushing them. Name the specific papers and what they show is now achievable.]

### 7.2 Speculative but Promising
[Ideas or approaches that are too nascent to have a clear paper trail, but that follow logically from open problems or current trends. Be explicit that these are the reviewer's projection, not established consensus.]

---

## 8. Conclusion

[3 focused paragraphs:]
[1. What the field has achieved and what the current frontier looks like.]
[2. The most important open problems and why they are hard.]
[3. The most likely directions for near-term progress and what kind of work would advance them.]

---

## References

[Full bibliography. Format each entry as:]
[Author(s)] ([Year]). *[Full Title]*. [Venue]. [arXiv:XXXX.XXXXX] or [DOI: ...]

Rules:
- Sort alphabetically by first author's last name
- In the bibliography, list all authors (do not truncate)
- Inline citations: (LastName et al., Year) for 3+ authors; (LastName & LastName, Year) for 2 authors; (LastName, Year) for solo author
- If a paper appeared both as an arXiv preprint and in a peer-reviewed venue, list the venue as the primary entry and include the arXiv ID as supplementary; use the publication year as the citation year
- arXiv IDs in canonical format: YYMM.NNNNN (e.g., `arXiv:1706.03762`) — no trailing version numbers
```

#### B. Individual Paper Summaries

For each included paper, create `reviews/<domain-slug>/summaries/<author>_<year>_<shortname>.md`:

```markdown
# [Full Paper Title]

**Authors**: [All authors]
**Year**: [Publication year; note preprint year if different]
**Venue**: [Conference / journal / arXiv-only]
**arXiv / DOI**: [Canonical ID]
**Citations**: ~[N] (as of [date checked])

---

## TL;DR
[1–2 sentences: what the paper does and why it matters.]

## Problem
[What specific problem does this paper address? What was inadequate about prior approaches?]

## Method
[Key technical approach. Be precise: architecture names, loss functions, datasets used for training.]

## Results
[Main quantitative findings. Include specific numbers: benchmark names, scores, comparison to baselines.]

## Key Contributions
[Bullet list of what this paper adds that was not available before: method, dataset, benchmark, theoretical result, empirical finding.]

## Significance
[Why this paper matters for the domain. What did it enable or change?]

## Limitations
[Weaknesses acknowledged by the authors, plus any apparent from reading. Be specific.]

## Relationships
- **Builds on**: [Prior works this paper explicitly extends or responds to, with a brief note on how]
- **Positioned against**: [Contemporaneous works this paper explicitly contrasts itself with]
- **Followed up by**: [Other papers in this review that cite this one as motivation or a baseline — fill in after reading all papers]
```

Also create/update `reviews/<domain-slug>/summaries/README.md` as an index of all included papers, sorted by year, with a one-line summary and a note of which theme in the main review each paper belongs to.

### 8. Citation Verification Checklist

Before finalising any output, perform these checks in order:

**Step A — Registry completeness**
- Every paper named in any output file appears in the master citation registry
- Every registry entry appears in the References section
- Every registry entry is cited at least once in the body

**Step B — Inline citation accuracy**
For each `(Author et al., Year)` in the body:
- Confirm the lead author's last name matches the bibliography entry exactly (check spelling)
- Confirm the year matches the bibliography entry — use publication year, not preprint year, consistently
- Confirm author-count formatting: "et al." only for 3+ authors; "Author & Author, Year" for exactly 2; "Author, Year" for solo papers

**Step C — Identifier verification**
- Every arXiv ID in the bibliography is in canonical format (YYMM.NNNNN, no trailing `v1`, `v2`, etc.)
- For at least 3 randomly selected papers, fetch the arXiv abstract page to confirm the paper exists and the title matches

**Step D — Coverage check**
- Each thematic subsection in Section 4 cites at least 3 papers
- Section 3 (Historical Arc) cites at least 5 papers spanning at least two distinct time periods
- The State of the Art table (Section 5.1) names at least 2 approaches with citations
- Each gap listed in Section 6 either cites a paper or is explicitly flagged as the reviewer's inference

**Step E — Formatting consistency**
- Papers appearing both as preprints and in venues are formatted consistently throughout (venue primary, arXiv supplementary, publication year used)
- Author name formatting in the bibliography is consistent throughout

## Notes

- Be honest about quality: if a paper has no clear contribution or makes dubious claims, say so explicitly rather than giving it equal billing.
- Prefer synthesis over description — every paragraph should answer "so what?" not just "what."
- The Historical Arc (Section 3) and Thematic Synthesis (Section 4) serve different purposes: the former is chronological (how did we get here), the latter is conceptual (what are the big ideas and how do they relate). Both are essential; do not collapse them.
- Use connective language throughout the synthesis to make inter-paper relationships explicit: "Building on...", "In response to...", "This was later shown to...", "A direct successor of this work..."
- If you cannot verify a paper's existence via its identifier, do not include it. It is better to review 12 verifiable papers than 15 where 3 are uncertain.
- Use precise technical language appropriate to the domain. Do not simplify to the point of inaccuracy.
