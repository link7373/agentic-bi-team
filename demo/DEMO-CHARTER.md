# Demo Charter — Northwind Analytics (fictional)

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> A pre-filled `START-HERE.md` for evaluating the kit without wiring a warehouse.
> `/setup-team` uses this as the charter when you choose demo mode. Everything below
> describes a company that does not exist, backed by data generated on your machine by
> `python demo/generate_demo_data.py`.
>
> **This is synthetic data.** Nothing here is a benchmark, and no number produced from
> it means anything about a real business. When you're ready for the real thing, fill in
> the actual `START-HERE.md` and re-run `/setup-team`.

---

## 1. The business

**What we do:** Northwind Analytics sells a subscription SaaS product that helps
mid-sized companies monitor their supply chain — shipment tracking, supplier scorecards,
and delay alerts. Customers connect their logistics systems and get dashboards and alerts.

**Customers:** ~800 companies, from two-person operations on the Starter plan to large
enterprises. Three segments: SMB (Starter plan), Mid-Market (Growth and Scale plans), and
Enterprise. Industries skew toward Retail, Manufacturing, and Logistics.

**Industry:** B2B SaaS / supply chain software.

**Competitors:** two well-funded venture-backed startups, and the incumbent ERP vendors
who bundle a weaker version of this for free.

**How we make money:** monthly and annual subscriptions on four plans — Starter $49,
Growth $299, Scale $999, Enterprise $2,500 per month. Expansion revenue comes from
customers upgrading plans as they add suppliers.

**Top three priorities this year:**
1. Reduce churn in the SMB segment — it is the largest customer count and the leakiest.
2. Grow net revenue retention by moving Growth customers up to Scale.
3. Understand which product usage patterns predict renewal, so Customer Success can
   intervene before a customer leaves rather than after.

**The one number that tells us if we're healthy:** net revenue retention.

## 2. The data

**Where it lives:** a single SQLite database at `demo/demo.db` containing five tables.

**How Claude Code reaches it:**

```bash
python demo/query_demo.py "SELECT COUNT(*) FROM dim_customer"
```

Read-only — the connection is opened in SQLite immutable mode. Also queryable with the
`sqlite3` CLI if you have it.

**Tables:**

| Table | Grain | What it holds |
|---|---|---|
| `dim_customer` | one row per customer | company, industry, country, segment, plan, acquisition channel, signup and churn dates, active flag |
| `fct_subscription_events` | one row per subscription change | new / upgrade / downgrade / churn, with the MRR delta |
| `fct_invoices` | one row per invoice | customer, invoice date, billing period month, amount, status (paid/open/failed) |
| `fct_product_events` | one row per customer / date / feature | fortnightly sample of feature usage counts |
| `fct_support_tickets` | one row per ticket | created and resolved dates, severity, whether it was reopened |

**Size:** roughly 50,000 rows across two years. Nothing here is slow.

**Known data problems:** unknown — that's part of what we want the team to tell us. (It
will find some.)

## 3. Metrics & reporting

**What we measure today:** MRR, customer count, and monthly churn count, tracked in a
spreadsheet that someone updates by hand. No agreed definitions, which is why two people
quoting "churn" often disagree.

**Questions we can't answer today:**
- Which customers are about to churn, early enough to do something about it?
- Is churn actually getting worse, or does it just feel that way?
- Which acquisition channel produces customers who stay?
- Does support-ticket volume predict churn, or just correlate with company size?

**Who reads reports:** a CEO who wants one number and a recommendation, a Head of
Customer Success who wants a list of at-risk accounts she can act on this week, and a
Head of Product who wants to know which features retain.

**Cadence:** weekly scorecard on Monday, monthly with a written narrative.

## 4. Tools & outputs

**Dashboard tool:** none yet — self-contained HTML dashboards are fine.

**Deliverable formats:** Markdown and Excel. Slides occasionally, for the monthly review.

**Branding:** none; use the standards' defaults.

## 5. Advanced analytics

**What we'd like to predict:** which customers will churn in the next 90 days, and what
distinguishes them. Any Python environment is fine.

## 6. Rules & boundaries

**Privacy:** the data is synthetic, so nothing is sensitive. Treat the fictional company
names as if they were real customers anyway — aggregate to groups of at least 5 in any
shared artifact, so the demo behaves the way a real deployment would.

**Never without asking:** anything that writes to the database (it is read-only, so this
should error rather than happen).

**Pre-authorised:** everything read-only. Go and explore.

## 7. Context & quirks

**Fiscal year:** calendar. **Timezone:** UTC. **Currency:** USD.

**Jargon:** "logo churn" means a customer leaving; "revenue churn" means the MRR they
took with them. They move differently here, which is the point.

**Day-one context:** we raised the Starter plan price earlier this year. Opinions differ
internally on whether it hurt us.

---

## Spoilers — what's planted in the data

> **Stop here if you want to evaluate the team honestly.** Run `/scorecard weekly`, then
> `/investigate-metric churn`, and see what it finds before you read this.

<details>
<summary>Three findings are deliberately in the demo data. Click to reveal.</summary>

1. **A segment-concentrated churn spike.** Roughly seven months before the end of the
   data, SMB/Starter churn roughly triples — the price rise mentioned in §7. At the same
   time Enterprise retention quietly *improves*, so the blended churn rate rises only
   modestly. Anyone who reports the topline alone will conclude "churn is up a bit" and
   miss that one segment is bleeding. That is Simpson's paradox doing exactly what
   `analytics.md` Part 1 warns about, and a good analyst stratifies before concluding.

2. **Two data-quality defects.** `fct_product_events` has a nine-day gap about three
   months before the end — a silent pipeline outage, which will look like an engagement
   collapse to anyone who doesn't check freshness first. And one month of `fct_invoices`
   contains duplicate rows for about 6% of customers: same customer, same billing period,
   a distinct `invoice_id`, so a primary-key uniqueness check passes while revenue for
   that month is inflated. Declaring the grain and testing it, rather than trusting the
   key, is what catches it.

3. **Seasonality.** Signups sag in December and July. A month-over-month comparison in
   January therefore reads as a collapse, and a year-over-year comparison reads as fine.
   Which one you use changes the story, which is why the reporting standards insist on an
   anchored comparison.

A team that finds all three — and says which one is a data problem before treating any of
them as a business result — is working the way this kit intends.

</details>
