---
name: make-deliverable
description: Produce a stakeholder-ready deliverable from completed analysis — PowerPoint/Google Slides deck, Word/Google Doc report, or Excel/Google Sheets workbook — with pyramid structure, takeaway titles, and every figure traceable to source. Use for any output going to humans beyond the team.
---

# Make Deliverable

Owner: `insights-communicator`. Args name the source analysis and format, e.g. `/make-deliverable Q2 churn analysis as exec deck`.

## Procedure

1. **Identify source and audience.** Source: a `FINDINGS.md` (or scorecard/model card) — if the analysis doesn't exist yet, run `/analyze` first; this skill packages, it doesn't analyse. Audience: from `knowledge/stakeholders.md` — their altitude, preferences, and format default ({{DELIVERABLE_FORMATS}}).

2. **Outline the storyline** (pyramid principle): governing answer → 2–4 supporting points → evidence. Every section title is a full-sentence takeaway. For board/external/high-stakes audiences, show the user the outline before full production.

3. **Produce the artifact** into `deliverables/YYYY-MM-DD-<slug>/`:
   - **PowerPoint:** `python-pptx`. Slide 1 = executive summary that stands alone. One idea per slide; takeaway-sentence titles; charts via matplotlib in the standard palette (`standards/reporting-standards.md`), embedded as images.
   - **Word/Docs:** `python-docx`. Executive summary ≤1 page → findings → recommendation → methodology appendix.
   - **Excel/Sheets:** `openpyxl`. Sheet 1 = formatted Summary; data sheets with frozen headers and proper number formats; final Notes sheet (sources, refresh date, definitions).
   - **Google Workspace native:** if access is configured ({{GOOGLE_WORKSPACE_ACCESS or "not configured"}}), create directly; else deliver the Office-format file ready to upload.
   - **Markdown/PDF:** for internal audiences; convert when asked.
   Install needed Python packages if absent.

4. **Integrity pass.** Create `SOURCES.md` mapping every key figure in the deliverable to its query/analysis file. No number without a source. Caveats included proportionately — footnote-level unless a caveat changes the conclusion (then it's a headline).

5. **Quality pass.** Honest axes (bars from zero), consistent rounding and precision, comparisons anchored ("vs Q1", "vs target"), brand/format rules applied ({{BRAND_GUIDELINES or "clean defaults"}}), the first page passes the stand-alone test.

6. **Deliver.** Send the file(s) to the user. Distribution beyond the user (email, shared drives, external parties) is outward-facing — confirm first unless pre-authorised in `CLAUDE.md` §8.

---

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373
