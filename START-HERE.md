# BI Team Project Charter

> **How to use this:** Write your answers in plain English under each question — bullet points, half-sentences, brain dumps all fine. You don't need to know technical terms. Leave anything blank if you don't know it; the team will ask or use sensible defaults. When you're done, run `/setup-team` in Claude Code and it will configure the entire BI team from this document.

---

## 1. The Business

**What does your company/organisation do? Who are your customers?**

> _Your answer here..._

**What industry are you in, and who are your main competitors?**

> _Your answer here..._

**How do you make money?** (subscriptions, one-time sales, ads, transactions, usage fees, etc.)

> _Your answer here..._

**What are your top 3 business priorities for the next 6–12 months?** (e.g. "grow paid signups", "reduce churn", "launch in new market", "cut costs")

> _Your answer here..._

**If you could only watch ONE number to know if the business is healthy, what would it be?** (Don't worry if you're not sure — the team can propose one.)

> _Your answer here..._

## 2. Your Data

**Where does your data live?** List everything you know about: databases, data warehouse, spreadsheets, SaaS tools (Stripe, Salesforce, Shopify, Google Analytics, HubSpot...), CSV exports, APIs. Rough is fine.

> _Your answer here..._

**How big is the data, roughly?** (hundreds of rows? millions? billions? "no idea" is a valid answer)

> _Your answer here..._

**How does Claude Code connect to your data?** (e.g. "there's a `psql` command that works", "we have a BigQuery MCP server", "I'll paste CSVs in", "I don't know — help me set this up")

> _Your answer here..._

**Any known data problems?** (duplicates, missing history, two systems that disagree, fields nobody trusts...)

> _Your answer here..._

## 3. Metrics & Reporting

**What do you measure today, if anything?** (existing reports, dashboards, KPIs — even informal ones)

> _Your answer here..._

**What questions do you wish you could answer but currently can't?**

> _Your answer here..._

**Who reads the reports?** For each audience, roughly: who they are, what they care about, how technical they are. (e.g. "CEO — wants one page, hates jargon", "marketing team — wants channel detail")

> _Your answer here..._

**When do you want recurring scorecards?** (e.g. "weekly every Monday morning, monthly on the 1st" — or "no recurring reports yet")

> _Your answer here..._

## 4. Tools & Outputs

**Which dashboard tool do you use or want to use?** (Tableau / Power BI / Looker / Looker Studio / something else / none — recommend one for me)

> _Your answer here..._

**What format do you want deliverables in?** (Google Slides / PowerPoint / Word / Google Docs / Excel / Google Sheets / Markdown / PDF)

> _Your answer here..._

**Any branding or formatting requirements?** (company colours, logo, template files, "always include a summary page", etc.)

> _Your answer here..._

## 5. Advanced Analytics & ML

**Any predictions or models you'd find valuable?** (e.g. "which customers will cancel", "sales forecast", "demand by region" — or "not sure, suggest some")

> _Your answer here..._

**What Python/tooling environment is available?** (e.g. "Python with pandas/scikit-learn installed", "whatever you set up", "I don't know")

> _Your answer here..._

## 6. Rules & Boundaries

**Any privacy/compliance rules the team must follow?** (GDPR, HIPAA, PIPEDA, "no customer names in reports", internal policies...)

> _Your answer here..._

**Anything the team should NEVER do without asking you first?** (e.g. delete data, email people, spend money on APIs, publish dashboards)

> _Your answer here..._

**Anything the team is pre-authorised to do freely?** (e.g. read any table, create scratch tables in a dev schema, run queries up to X cost)

> _Your answer here..._

## 7. Context & Quirks

**Fiscal year, timezone, currency?** (e.g. "calendar year, Pacific time, CAD")

> _Your answer here..._

**Company jargon decoder.** Any internal terms, acronyms, product codenames the team should know? (e.g. "'MAU' here means weekly actives, confusingly"; "'Atlas' is our enterprise product")

> _Your answer here..._

**Anything else a new head of BI should know on day one?** (politics, history, past failed projects, strong opinions held by leadership...)

> _Your answer here..._

---

*When finished: save this file, then run `/setup-team` in Claude Code.*
