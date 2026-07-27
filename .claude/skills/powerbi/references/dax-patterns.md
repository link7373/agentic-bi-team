# DAX — thin measures over a clean model

> The team's position: **DAX is a presentation layer, not a transformation layer.**
> Complexity belongs upstream in a mart where it is testable, reusable, and visible
> in `analyses/`. This is `CLAUDE.md` principle 7 applied to Power BI.

## Naming is not negotiable

Every measure name must match `knowledge/metrics-catalog.md` **character for
character**. Not "close enough" — identical. The catalog is the single definition
(`CLAUDE.md` principle 2), and the moment a dashboard shows `Revenue` while the
catalog says `Net Revenue`, somebody is comparing two numbers that were never the
same thing.

If the metric you need isn't in the catalog, stop and route through `/define-kpis`
and `metrics-steward`. Do not invent a definition inside a measure — that's how
organisations end up with four revenue numbers and no way to reconcile them.

Document the link in the measure description, where it shows up in Desktop's field
list:

```tmdl
	/// Net revenue after discounts and returns. Catalog: net_revenue.
	measure 'Net Revenue' = SUM(Sales[net_amount])
		formatString: \$#,##0
```

## Build on base measures

Define the metric once; derive everything else from it.

```tmdl
	measure 'Net Revenue' = SUM(Sales[net_amount])

	measure 'Net Revenue LY' =
			CALCULATE([Net Revenue], SAMEPERIODLASTYEAR('Date'[Date]))

	measure 'Net Revenue YoY %' =
			VAR current = [Net Revenue]
			VAR prior = [Net Revenue LY]
			RETURN DIVIDE(current - prior, prior)
		formatString: 0.0%
```

Change the definition of net revenue once and every derived measure follows. Repeat
`SUM(Sales[net_amount])` in twelve places and you have twelve things to update and
eleven you'll miss.

## Patterns worth knowing

**`DIVIDE`, never `/`.** `DIVIDE(a, b)` returns blank on divide-by-zero instead of an
error. A single zero denominator otherwise breaks the whole visual.

**Fully qualify columns, never qualify measures.** `Sales[amount]` and `[Net Revenue]`.
This is the community convention and it makes the two visually distinguishable —
worth following precisely because DAX won't stop you doing the opposite.

**`VAR` for anything non-trivial.** Variables evaluate once, in the filter context
where they're declared. They make intent legible and prevent accidental re-evaluation
under a changed context.

**`SELECTEDVALUE` over `VALUES`** when you want a single value with a graceful
fallback: `SELECTEDVALUE(Product[category], "All categories")`.

**Format in `formatString`, not in DAX.** `FORMAT()` returns text, which then sorts
alphabetically and won't chart. This surprises people repeatedly.

## Things that quietly go wrong

**`CALCULATE` replaces filters; it doesn't add to them.** `CALCULATE([Revenue], Product[category] = "A")`
overrides any existing category filter. To narrow within the current context use
`KEEPFILTERS`.

**Percentages don't sum.** A measure defined as an average of ratios gives the wrong
total row. Compute the ratio from summed numerator and denominator instead —
`DIVIDE(SUM(numerator), SUM(denominator))`. This is Simpson's paradox arriving
through the back door (`analytics.md` Part 1), and the total row is usually where
someone notices.

**Time intelligence needs a real date table**, marked as such, contiguous. Without it
`SAMEPERIODLASTYEAR` and `DATESYTD` return subtly wrong results at period edges
rather than failing.

**Blank ≠ zero.** A blank measure hides its row in a visual; zero shows it. Decide
which you want and be explicit — `+ 0` or `COALESCE` — rather than discovering it in
a review.

**Bidirectional relationships plus `CALCULATE` produce ambiguous filter paths.** The
symptom is a believable wrong number. Prefer single-direction and explicit
`CROSSFILTER` where genuinely needed.

## When a measure is getting long

Ten lines of DAX with nested `FILTER`s over a large fact table is a signal, not an
achievement. Ask:

1. Can this be a column in the mart? Push it to `analytics-engineer`.
2. Is it slow because the model is wrong — snowflaked, wrong grain, missing star?
3. Is it business logic that belongs in the catalog rather than in one report?

`standards/powerbi-standards.md` sets the ceiling: no measure should need a paragraph
to explain. The existing rule in `dashboard-developer` — no 200-line calculated
fields — applies here in full.

## Validating

`validate_pbip.py` checks that every field a visual binds to exists in the model, but
it does **not** evaluate DAX — it can't tell you a measure is wrong, only that it's
referenced. Correctness still requires opening Desktop and reconciling against a
direct query, which is `/powerbi` step 8 and not optional.

At Tier 3, `fab` can run DAX queries against a published model for automated
reconciliation. Until then, reconcile by hand and save the query in
`dashboards/<name>/checks/`.
