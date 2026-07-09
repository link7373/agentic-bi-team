# Analytics Reference

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373


This file is the BI team's standing analytical framework for data analysis, insight writing, and visualization.

Referenced in analyses, scorecards, reports, dashboards, and any work involving interpreting or presenting data.

---

## Part 1: Statistical Reasoning

### The Distributions Rule

The shape of a distribution determines what's normal, what's extreme, and how extreme the extremes can be.

**Gaussian (normal):** Symmetric bell curve. Produced when many independent additive factors contribute (e.g., height). Outliers are rare and bounded — in a Gaussian world, someone 4 standard deviations from the mean is remarkable but finite.

**Lognormal:** Produced when many factors multiply together, or when growth is proportional to current size (e.g., body weight, income, running speed, chess ratings). Skewed right — the upper tail is much longer than Gaussian. Outliers are far more extreme than people expect.

**Power-law / heavy-tailed (log-t):** Produced by cascading processes, self-organized criticality, or scale-free networks (e.g., disaster costs, earthquake magnitudes, solar flares, stock market crashes). Outliers are catastrophically larger than lognormal would predict. The "100-year event" is not rare — it's just that the distribution has no meaningful upper bound.

**Practical rule:** Before characterizing data, plot the distribution. If the data looks lognormal, model it as lognormal. If extreme events seem more frequent than lognormal predicts, consider a heavy-tailed model. Never use a Gaussian model for disaster, wealth, or viral growth data — you will systematically underestimate tail risk.

---

### Nobody Is Average

When you measure people on multiple dimensions simultaneously, almost no one is "average" on all of them. Gilbert Daniels showed this with ANSUR military data: out of 4,063 airmen, *zero* were within the "average" range on all 10 body measurements.

**Why it matters for demographics:** "The average household in V8W earns $87,000 and has 2.3 people" describes no real household. When analyzing demographic data, always break populations into segments. Report distributions, not just means.

**The multidimensional trap:** Any two-group comparison (e.g., renters vs. owners) will have the groups diverge dramatically across many other dimensions. The "average renter" is a statistical fiction.

---

### Inspection Paradox (Length-Biased Sampling)

The way you sample data determines what you observe. If you sample *during an event*, you systematically oversample long events.

**Classic examples:**
- Ask students how large their class is → they report larger classes than the dean's records show (students are more likely to be *in* a large class).
- Ask a random person in prison how long their sentence is → they overestimate typical sentences (you're more likely to find long-term prisoners at any random point in time).
- A random subway passenger waits longer than the average train interval (they're more likely to arrive during a long gap).
- Your Facebook friends have more friends than you do (you're more likely to be friends with popular people).

**Recidivism:** The "45-50% of released prisoners re-offend within 3 years" statistic uses event-based sampling (selecting from a release event). Individual-based sampling gives ~28%. Both are correct; they answer different questions. Choose the sampling method that matches the question.

**Practical rule:** Always ask: *how was this sample collected?* If events, behaviors, or durations drove selection, assume the sample overrepresents long or frequent events.

---

### Simpson's Paradox

A trend visible in every subgroup can reverse or disappear in the aggregate. Conversely, an aggregate trend can be absent in every subgroup.

**Mechanism:** A confounding variable (e.g., age) is correlated with both the grouping variable and the outcome. As the composition of the aggregate changes over time (e.g., an aging population), the aggregate trend shifts even if every individual subgroup trend is opposite.

**Real-world examples:**
- American optimism: *increased* within every birth cohort over their lifetimes, but *decreased* in the aggregate because pessimistic younger cohorts replaced optimistic older ones.
- Real wages: *increased* within every education level, but *decreased* in the aggregate because the workforce shifted toward lower-education brackets.
- COVID vaccines: vaccinated people in the 10-59 age band appeared to die at *higher* rates than unvaccinated — because older people in that band were both more likely to be vaccinated AND more likely to die of any cause. Within each 5-year age bracket, vaccinated people died at lower rates in every single bracket.

**Diagnosis checklist:**
1. Is the aggregate trend surprising or counterintuitive?
2. Is there a compositional shift in the population over time?
3. When you stratify by the likely confound, does the paradox disappear?

**Practical rule:** Never report an aggregate trend without checking for Simpson's paradox. Always stratify by the key confounding variable before drawing conclusions. This is especially critical in demographic analysis where age, income, and geography are all correlated with each other.

---

### Base Rate Fallacy

When interpreting the result of a test (statistical, medical, algorithmic), most people ignore the prior probability (base rate) of the condition being tested. This causes dramatic overestimation of the significance of positive results.

**Formula:**
- Sensitivity = P(positive test | actually positive)
- Specificity = P(negative test | actually negative)
- **Positive predictive value** (what you care about) = P(actually positive | positive test)

The positive predictive value depends critically on the **base rate** — what fraction of the tested population actually has the condition.

**Worked example:** A test with 87% sensitivity and 98% specificity applied to a population with 1% prevalence yields only a 30% positive predictive value — 70% of positive results are false positives.

**Applications:**
- Composite index comparisons: a segment with a "high" index score usually contains many ordinary members and a few extreme ones — don't equate the aggregate with any individual member.
- Any score used as a screening tool: a "below average" score means bottom-half of the reference population, not "bad" in absolute terms — what the reference base rate actually represents matters enormously.
- Any model predicting outcomes for people or accounts: the base rate determines what a positive prediction actually means.

---

### Collider Bias / Berkson's Paradox

When two independent causes both affect whether something is included in your sample (or analysed), you get spurious correlations between those causes *within* the sample.

**The low-birthweight paradox:** Maternal smoking causes low birthweight. Birth defects also cause low birthweight. In the general population, smoking and birth defects are uncorrelated. But among low-birthweight babies, if the baby is low-weight due to a birth defect, they are *less* likely to have a smoking mother. So smoking appears "protective" within the low-birthweight group — a complete statistical artifact.

**Other examples:**
- Hospital patients with diabetes appear *less* likely to have cholecystitis — because if they're in the hospital without diabetes, cholecystitis is more likely to be why.
- Restaurants in bad locations appear to have *better* food than restaurants in good locations — bad food + bad location = closed; survivors in bad locations are self-selected for quality.
- Tall athletes are not as smart as short athletes (within the NBA) — because to reach the NBA as a shorter player requires exceptional skill compensating for height.

**The obesity paradox:** Obese patients with certain diseases appear to have *better* outcomes — actually a collider bias where other risk factors are the real cause.

**Causal diagram test:** If two arrows both point *into* the same variable (a "collider"), conditioning on that variable (i.e., restricting your sample to it) creates a spurious correlation between the two causes.

**Practical rule:** When a finding seems counterintuitive or paradoxical, check whether the analysis was restricted to a selected subgroup. If so, collider bias is a likely explanation.

---

### Long Tails and Disaster

The distribution of disaster sizes (hurricane costs, earthquake magnitudes, solar flares, stock market crashes, asteroid craters) follows distributions longer-tailed than lognormal — typically a log-t distribution.

**Why this matters:**
- Gaussian thinking: "the once-in-100-years event" has a well-defined magnitude.
- Lognormal thinking: extreme events are larger than Gaussian predicts, but still bounded in a meaningful sense.
- Power-law/log-t thinking: there is no meaningful upper bound; events 10x or 100x the historical maximum are not negligible in probability.

**Black swans and gray swans:** Nassim Taleb's "black swans" are events that seem extremely unlikely given a Gaussian model but are predictable given a heavy-tailed model. "Gray swans" are events that *are* predictable from heavy-tailed models — catastrophic but not truly unprecedented in structure.

**In practice:** Risk and severity scores should be read as ordinal categories, not precise probabilities. A "Moderate" rating doesn't mean a catastrophic outcome is impossible — it means the item sits in the middle tier of the reference population. The tail risk for worst-case events (outages, fraud losses, demand spikes) is always larger than intuition suggests.

---

### Fairness and Algorithmic Bias

Different mathematical definitions of fairness are mutually incompatible when base rates differ between groups.

**Two definitions of a fair algorithm:**
1. **Equal error rates:** Same false positive rate and false negative rate for all groups.
2. **Equal predictive value:** A "high risk" prediction means the same probability of the outcome in all groups.

**The incompatibility theorem:** If the base rate of the outcome differs between groups (e.g., different recidivism rates), you cannot simultaneously achieve equal error rates AND equal predictive values. Any algorithm that achieves one will violate the other.

**Practical implication:** When evaluating any algorithmic scoring system, be clear about *which* fairness criterion is being optimised, and be honest that it cannot simultaneously satisfy the others.

---

### Age-Period-Cohort Analysis

Changes in population statistics over time can be explained by three distinct mechanisms:

- **Age effect:** Something that happens to most people at a particular life stage (e.g., increased conservatism around age 30).
- **Period effect:** Something that affects everyone at the same historical moment (e.g., a major economic shock, a social movement in 1990).
- **Cohort effect:** Something that permanently differentiates one generation from another (e.g., Generation X vs. Baby Boomers).

**The key test:**
- If the effect is an *age* effect, it appears at roughly the same age in all cohorts.
- If it's a *period* effect, all cohorts shift simultaneously at the same historical moment.
- If it's a *cohort* effect, each successive generation is consistently different from the last.

**Practical rule:** When comparing demographic metrics across time (e.g., income trends, crime trends), always ask which of these mechanisms is driving the change. Cohort effects and period effects can produce Simpson's paradox-style reversals in aggregate trends.

---

### Regression to the Mean

Extreme measurements tend to move toward the mean on subsequent measurement. This is a mathematical property of correlation, not a causal mechanism.

**Common mistakes:**
- Treating regression to the mean as a genuine improvement ("the treatment worked" when random variation explains the recovery).
- Medical interventions are most often applied when patients are at their worst — subsequent improvement is partly regression to the mean.
- Top-performing communities on any metric tend to perform less extremely the next measurement period.

**In practice:** Composite and component scores regress toward the population mean over successive measurements. A segment that scores 85 one period is unlikely to score 85 the next — not because anything changed, but because extreme scores partially reflect measurement noise.

---

## Part 2: Visualization Principles

### Preattentive Attributes

The brain processes these in under 250 milliseconds, before conscious attention kicks in. Use them deliberately to guide the reader's eye.

| Attribute | Best for |
|---|---|
| **Length** | Quantitative comparison (bar charts) — most accurate preattentive encoding |
| **Position** | Quantitative comparison (scatterplots, dot plots) — very accurate |
| **Color (hue)** | Categorical distinction — one color per category |
| **Color (intensity)** | Sequential quantitative encoding — light to dark |
| **Size** | Rough relative magnitude — imprecise; avoid for precise comparison |
| **Shape** | Categorical distinction — limited to ~5-6 shapes; use sparingly |

**Rule:** Use one or two preattentive attributes per chart. More than two creates visual noise that cancels the preattentive advantage.

---

### Types of Data

| Type | Description | Example | Encoding |
|---|---|---|---|
| **Categorical (nominal)** | Labels without order | Region, channel, plan tier | Color hue, position, shape |
| **Ordinal** | Ordered categories | Risk level (Low/Moderate/High/Severe), star rating | Position, ordered color scale |
| **Quantitative (discrete)** | Exact countable numbers | Number of orders, seat count | Length, position |
| **Quantitative (continuous)** | Infinite possible values | Revenue, duration, composite score | Length, position, color intensity |

---

### Chart Selection Guide

**For comparison across categories:**
- **Bar chart** — Default choice. Encodes value as length from a common zero baseline. Handles many categories if sorted.
- **Dot plot** — When exact lookup is less important than seeing the spread. More elegant for many items.
- **Lollipop chart** — Visual compromise between bar chart precision and dot plot elegance.

**For distribution:**
- **Histogram** — Shows frequency distribution. Use when you need to show the shape of the data.
- **Box plot** — Compact summary (median, quartiles, range). Clinical-looking but information-dense.
- **Jitter plot (jitterplot)** — Shows individual points plus distribution. Best for comparing an individual to a peer group.

**For relationships between variables:**
- **Scatterplot** — Two quantitative variables. Each dot is one observation.
- **Small multiples** — Same chart repeated across categories (break one crowded scatterplot into facets).

**For time:**
- **Line chart** — Default for continuous time series. Shows trend.
- **Slope chart** — Compares exactly two points in time across many categories.
- **Bump chart** — Shows *rank* over time (not value). Good for competitive standings.
- **Index chart** — Compares growth rates of events that start at different times (x-axis = days since start, not calendar date).
- **Cycle plot** — Shows within-period patterns AND between-period trends simultaneously (e.g., hourly patterns by day of week).
- **Heat map / highlight table** — Two time dimensions simultaneously (e.g., month × hour of day, year × day of year).

**For actual vs. target:**
- **Bullet graph** — The best single chart for this. Actual value as a bar, target as a line, performance bands as shading.

**For geographic data:**
- **Choropleth map** — Shaded regions (e.g., territories by revenue). Use sequential or diverging color.
- **Symbol map** — Proportional circles at point locations. Use only for rough comparison — circles are hard to read precisely.

**For process / duration:**
- **Gantt chart** — Duration of events on a timeline.
- **Jump plot** — Bottleneck analysis in event sequences.

---

### Charts to Avoid (and Why)

| Chart | Problem | Replacement |
|---|---|---|
| **Pie chart** | Humans cannot accurately compare angles or arc lengths; comparison across pies is nearly impossible | Sorted bar chart |
| **Donut chart** | Same as pie, plus a hole | Bullet graph (for single KPI) or bar chart |
| **3D bar/pie** | Distorts perceived lengths due to perspective | 2D bar chart |
| **Bubble chart (packed)** | Area is perceived as radius; differences of 10x look like 3x | Bar chart; use bubble size only as a rough secondary encoding on a scatterplot |
| **Word cloud** | Word size is meaningless as a precise quantity; position is decorative | Sorted bar chart with one highlighted bar |
| **Concentric donut / radial bar** | Makes comparison nearly impossible (arc lengths at different radii are incomparable) | Standard bar chart |

**Exception for pie:** Acceptable as a single KPI indicator showing progress toward a fixed 100% target (e.g., "64% of target reached") — but only if no precise comparison between categories is needed.

---

### Color Principles

**Use color with a purpose, not for decoration.**

| Color scheme | Use when | Example |
|---|---|---|
| **Sequential** (light → dark, one hue) | Single quantitative variable, all values go in one direction | Revenue by region on a map |
| **Diverging** (two hues meeting at midpoint) | Quantitative variable with a meaningful midpoint (e.g., 0, average, target) | Performance vs. target |
| **Categorical** (distinct hues) | Distinguishing categories — use ≤6 hues | Product-line groups |
| **Highlight** (one bold color, rest muted gray) | Drawing attention to one specific item without alarming | Highlighting one segment among many |

**Color blindness:** ~8% of men have color vision deficiency (CVD). Red-green is the most common impairment — both appear as brown. Use **blue-orange** as a color-blind-friendly alternative to red-green. Or use blue-orange-gray as a three-category palette.

If you must use red and green (e.g., client requires traffic-light colors), add a secondary encoding: directional arrows, icons, or text labels. Do not rely on color alone to convey meaning.

---

### Axis Rules

**Start at zero when:** The chart uses *length* to encode value (bar charts, area charts, stacked bars). Truncating the axis visually inflates differences.

**Not required when:** The chart uses *position* to encode value (line charts, scatterplots, dot plots). The goal is to show change and trend, not proportional magnitude. Truncating the y-axis on a line chart is acceptable when the goal is to show relative change rather than absolute magnitude — label clearly.

---

### Dashboard Design Principles

**Definition:** "A dashboard is a visual display of data used to monitor conditions and/or facilitate understanding."

**Key design decisions:**

1. **Identify the question before choosing the chart.** What is the audience trying to decide? Work backwards from the decision to the data to the chart.

2. **Every decision is a compromise.** A line chart shows trend; an area chart shows cumulative total — you cannot do both equally well in one chart. Choose what matters more.

3. **Make it personal.** Data is most engaging when the viewer sees themselves in it. Allow the viewer to identify their own data point within a distribution. This is why jitter plots showing "your score vs. peers" drive engagement.

4. **Functional before beautiful.** A dashboard decorated with packed bubbles and treemaps to avoid "boring bar charts" will confuse users and be abandoned. Analytical clarity is the foundation; aesthetic appeal is built on top of it.

5. **Beware the dead-end dashboard.** Review KPIs regularly — a metric that hits target consistently is no longer informative. Track dashboard usage. Talk to actual users about whether the questions it answers are still the right questions.

6. **Keep asking "why."** The Five Whys (Toyoda): when a dashboard surfaces an anomaly, ask why repeatedly until you reach a root cause, then act. A dashboard that answers one question should raise two more.

7. **Static vs. interactive:** A well-designed static dashboard forces prioritisation — you can't show everything. Interactive dashboards allow deeper exploration but require more from the user. Know your audience.

---

### The Squiggle of Visual Exploration

Data exploration is non-linear. A dashboard is a starting point, not an endpoint. The path from "here's the data" to "here's the insight" involves:
- noticing a pattern
- forming a hypothesis
- looking at a different cut
- disconfirming the hypothesis
- reforming it
- eventually arriving at a defensible claim

This squiggle of exploration should happen *before* publishing any insight. The published result shows the endpoint, not the messy path.

---

### Narrative & the Big Idea

Charts inform; **stories persuade and get remembered.** Once the analysis is done, communicating it is a separate craft:

1. **Understand the context first.** Before choosing any visual, know *who* the audience is, *what* you need them to know or do, and *how* you'll deliver it (live vs. sent-to-read change everything). The same finding becomes a different artifact for a different audience.

2. **The Big Idea — one sentence.** Compress the entire message to a single, complete, arguable sentence: your point of view, what's at stake, and the recommended action. If it won't compress, the thinking isn't finished.

3. **The 3-minute story.** You should be able to tell the whole thing out loud in three minutes with no visuals. The deck/report *supports* that story; it is not the story.

4. **Narrative arc, not a data dump.** Borrow story structure: **setup** (the context / status quo the audience accepts) → **tension** (what changed, the problem, what's at risk) → **resolution** (your recommendation and the evidence that earns it) → **call to action** (specific, owned). Tension is what makes an audience care; a list of charts has none.

5. **Repetition and the "so what."** State the takeaway, show the evidence, restate the takeaway. Every element that survives must serve the Big Idea — if it doesn't, cut it.

---

## Part 3: Applied Rules

These rules apply the principles above to the team's day-to-day output — analyses, scorecards, reports, dashboards, and deliverables.

### For Written Insights & Reports

1. **Lead with the paradox or surprise.** The most engaging opening is a finding that contradicts intuition. Then explain why the data actually makes sense.

2. **Check for Simpson's paradox before publishing any trend.** If you show an aggregate trend, stratify by the key confounder (segment, region, cohort, plan tier) and confirm it holds before reporting it.

3. **Name the distribution.** When discussing revenue, deal size, prices, durations, or usage — note whether the distribution is roughly normal, skewed right, or heavy-tailed. This gives readers the right intuition for what "above average" means.

4. **Report medians, not means, for skewed data.** Money and duration metrics are typically lognormal — the mean sits above what most cases experience. Use the median and label it clearly ("median order value", not the ambiguous "average").

5. **Always show the base rate.** When reporting a proportion (e.g., "30% of accounts are high-risk"), always name the comparison set: 30% of which population, versus what?

6. **Avoid the ecological fallacy.** Segment- or region-level statistics describe the group on average — they say nothing about any individual member within it. Never imply every member experiences the group-level number.

7. **Confidence language:** When data is sparse (small samples, suppressed cells), write "estimated" or "based on limited data." Never present suppressed or imputed data with the same confidence as fully sampled data.

### For Chart and Visualization Choices

1. **Default chart:** Sorted horizontal bar chart. It handles any number of categories, is readable at a glance, and communicates clearly.

2. **For peer / cohort comparison:** Jitter plot or dot plot with quartile bands and a highlighted marker for the item of interest. Add a KPI table below for exact values.

3. **For trends over time:** Line chart. Label the start and end points. If showing multiple dimensions simultaneously, consider a slope chart (two points) or cycle plot (cyclical patterns).

4. **For rankings:** Bump chart if the audience cares about rank over time. Sorted bar if they care about the current snapshot.

5. **For geographic data:** Choropleth map with a sequential single-hue scale. Use diverging color only when there is a meaningful neutral midpoint (e.g., vs. target or vs. prior year).

6. **Color palette:** Follow the brand and semantic rules in `standards/dashboard-standards.md` — sequential blue for magnitude, blue-orange for diverging, categorical hues sparingly. Always test with CVD (color-blindness) simulation before publishing.

7. **For composite / index scores:** Always show the component breakdown as a bar chart alongside the composite. The composite without its components is a dead-end — readers can't act on it without the drivers.

### Statistical Hygiene Checklist

Before publishing any data claim:

- [ ] Is the sampling method appropriate for the question?
- [ ] Have I checked for Simpson's paradox by stratifying?
- [ ] Am I reporting the right central tendency (mean vs. median) for this distribution?
- [ ] Is the base rate visible and named?
- [ ] Have I accounted for the inspection paradox (is my sample duration-biased)?
- [ ] Is there a collider variable that could be creating a spurious correlation?
- [ ] Are my axes starting at zero when length encodes value?
- [ ] Have I checked color accessibility?
- [ ] Does the chart title state the finding, not just describe the chart?
- [ ] Is this a causal or correlational claim? (Label clearly.)

---

## Quick Reference: Common Traps and Their Names

| Trap | What it is | Source |
|---|---|---|
| Simpson's paradox | Aggregate trend reverses in subgroups | Statistical reasoning — Part 1 |
| Base rate fallacy | Ignoring prior probability when interpreting test results | Statistical reasoning — Part 1 |
| Inspection paradox | Duration-biased sampling overrepresents long events | Statistical reasoning — Part 1 |
| Collider bias (Berkson's paradox) | Selecting on a shared effect creates spurious correlations | Statistical reasoning — Part 1 |
| Ecological fallacy | Applying group statistics to individuals | (standard) |
| Regression to the mean | Extreme values move toward the mean on re-measurement | (standard) |
| Lognormal confusion | Applying Gaussian intuition to skewed distributions | Statistical reasoning — Part 1 |
| Long-tail blindness | Underestimating tail risk with lognormal/Gaussian models | Statistical reasoning — Part 1 |
| Length-biased sampling | Selecting events by duration oversamples long events | Statistical reasoning — Part 1 |
| Preston's paradox | Family size appears to increase even when everyone has fewer children than their mother | Statistical reasoning — Part 1 |
| Pie/angle distortion | Humans misread angles and arc lengths | Visualization — Part 2 |
| Truncated y-axis | Starting bar chart above zero visually inflates differences | Visualization — Part 2 |
| Dead-end dashboard | Metrics that always hit target are no longer informative | Visualization — Part 2 |
| Bubble chart imprecision | Circle areas are systematically underestimated | Visualization — Part 2 |
