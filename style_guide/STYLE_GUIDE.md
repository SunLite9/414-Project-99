# STATS 414 Presentation and Plot Style Guide

Version 1.0 · October 27, 2026 · Team: Juan Cortes-Aguiar, Ravikiran Madichetty, Ashish Singh

This guide makes every deck, plot and report figure in the project look like it came from one team. It uses UCLA's official brand colors and fonts, and it is enforced in code: plots import `style_guide/ucla_style.py`, and decks are generated with the theme in `style_guide/deck_theme.json`. If you change a rule here, change it there too.

Sources for the brand values: [UCLA Brand: Colors](https://www.brand.ucla.edu/identity/colors), [UCLA Design System color tokens](https://designsystem.brand.ucla.edu/build/v2.6.0/docs/style-guide/colors.html), [UCLA Samueli typography guide](https://samueli.ucla.edu/style-guide-typography/). No UCLA logo or wordmark is used.

---

## 1. Principles

1. **One message per slide.** The slide title is the finding as a sentence ("No model beat the quoted price"), not a topic ("Model results").
2. **Blue field, gold accent.** UCLA's rule: "A field of blue with a gold accent says 'UCLA.' A field of gold with a blue accent does not." Blue dominates, gold is used sparingly, white is used generously.
3. **Honest charts.** Every chart compares against a benchmark (usually the market price), shows uncertainty where we have it, and states its data source.
4. **Readable from the back of the room.** Body text is never below 12 pt on a slide; chart text is never below 10.5 pt at the size it is shown.

## 2. Color

### 2.1 Brand palette (official UCLA values only)

| Role | Name | HEX | Use |
| --- | --- | --- | --- |
| Primary | UCLA Blue | `#2774AE` | Title-slide background, primary data series, key numbers |
| Primary | UCLA Gold | `#FFD100` | Accent on blue fields; highlight cards. Never text on white |
| Primary | White | `#FFFFFF` | Content-slide background |
| Secondary | Darker Blue | `#005587` | Slide titles on white, emphasized text |
| Secondary | Darkest Blue | `#003B5C` | Second data series, error bars, numbers on gold cards |
| Secondary | Lighter Blue | `#8BB8E8` | Fourth data series (always labeled) |
| Secondary | Lightest Blue | `#DAEBFE` | Card fills, table header on light slides |
| Secondary | Darkest Gold | `#FFB81C` | "Attention" data series (always labeled) |
| Neutral | Gray 80% | `#333333` | Body text |
| Neutral | Gray 60% | `#666666` | Secondary text, footers, tick labels |
| Neutral | Gray 40% | `#999999` | Reference marks (baselines, "implied by price") |
| Neutral | Gray 20% / 10% / 5% | `#CCCCCC` / `#E5E5E5` / `#F2F2F2` | Axis lines / grid lines / table banding |
| Alert only | Error / Success | `#D60000` / `#007339` | Error or success messages only; never a data series |

**UCLA rules we follow.** No tints (colors diluted with white) and no other shades of blue or gold. No gold text on Darkest Blue. No gray text on gold. The tertiary neon colors (yellow, green, magenta, cyan, purple) are not used.

### 2.2 Approved text and background pairs

Measured contrast ratios (WCAG AA needs 4.5:1 for normal text and 3:1 for large text, meaning 18 pt or 14 pt bold and larger):

| Text on background | Ratio | Allowed for |
| --- | --- | --- |
| Gray 80% on White | 12.6 | All text |
| Darker Blue on White | 7.9 | Titles, emphasis |
| UCLA Blue on White | 5.0 | Large numbers, labels ≥ 12 pt |
| Gray 60% on White | 5.7 | Secondary text, footers |
| White on UCLA Blue | 5.0 | Title-slide text |
| UCLA Gold on UCLA Blue | 3.4 | Large text only (≥ 18 pt or 14 pt bold) |
| White on Darker Blue | 7.9 | Table header text |
| Gray 80% on Lightest Blue | 10.4 | Card text |
| Darkest Blue on UCLA Gold | 8.1 | Numbers and labels on gold cards |
| Darkest Gold on White | 1.7 | **Never text.** Data marks only, with labels |

### 2.3 Data colors

| Job | Color | Rule |
| --- | --- | --- |
| The series the slide is about | UCLA Blue `#2774AE` | Default for a single series |
| The benchmark it is compared with | Gray 40% `#999999` | Price-implied values, baselines, "perfect calibration" lines (dashed) |
| Worse than benchmark / needs attention | Darkest Gold `#FFB81C` | Always with a direct value label (contrast 1.7:1 alone) |
| Second data series, error bars | Darkest Blue `#003B5C` | |
| Categorical order (2–4 series) | UCLA Blue → Darkest Gold → Darkest Blue → Lighter Blue | Fixed order, never cycled. More than 4 series: facet or fold into "Other" |
| Magnitude (one variable, low → high) | Lightest Blue → Lighter Blue → UCLA Blue → Darker Blue → Darkest Blue | UCLA's blue gradient; never a rainbow |
| Good / bad meaning | Blue = better, Gold = worse, Gray = no clear difference | Matches the model-comparison chart |

**Checked for color blindness.** The categorical order was run through the colorblind-safety validator in our charting tool, with simulated deuteranopia, protanopia and tritanopia. The worst adjacent pair stays well separated: ΔE 33.7, against a target of at least 8. The validator also flags Darkest Blue and Lighter Blue as low-chroma and Darkest Gold as very light. Those are UCLA's own colors and UCLA forbids substitutes, so we keep them and add secondary encoding instead: direct labels, distinct marker shapes, or gaps.

## 3. Typography

UCLA's brand fonts are Karbon (licensed, for print) and Helvetica/Arial. We use **Arial** everywhere: slides, plots and documents. It ships with every Mac and Windows machine, so decks look identical for all three of us. Plots fall back to Liberation Sans, which has the same letter widths, when Arial is missing (for example on Linux).

| Element | Size | Weight | Color |
| --- | --- | --- | --- |
| Title-slide title | 40–44 pt | Bold | White on UCLA Blue |
| Content-slide title | 26–28 pt, one line | Bold | Darker Blue |
| Section label above a title | 11 pt, all caps | Bold | UCLA Blue |
| Body text and bullets | 14 pt (12 pt minimum) | Regular | Gray 80% |
| Key number (stat callout) | 32–36 pt | Bold | UCLA Blue (Darkest Blue on a gold card) |
| Caption, source note, footer | 9–11 pt | Regular | Gray 60% |
| Plot axis labels / ticks / labels | 12 / 11 / 10.5 pt at final size | Regular | Gray 80% / Gray 60% / Gray 80% |

Sentence case everywhere ("Favorites won about as often as priced"), no periods at the end of titles, and left-aligned body text.

## 4. Slide system

Canvas: 16:9, 10 × 5.625 in. Margins: 0.5 in on all sides. Gaps between blocks: 0.25 in inside a group, 0.5 in between groups.

| Layout | Use | Look |
| --- | --- | --- |
| **Title** | First slide | UCLA Blue field; title in white; subtitle and names in white; one gold accent (the course label) |
| **Section / close** | Section breaks, takeaways | UCLA Blue field, white text, gold for the one forward-looking line |
| **Content** | Everything else | White; section label (11 pt caps, UCLA Blue) above a 28 pt Darker Blue title; footer "STATS 414 · deck name" and slide number in Gray 60% |

Building blocks:

- **Chart + takeaways:** chart on the left (5.3–6 in wide), one key number and 2–4 bullets on the right.
- **Stat callouts:** a big number with a one-line label under it, for headline figures.
- **Cards:** Lightest Blue rounded rectangles (radius 0.08 in), no border, no shadow, for parallel items (splits, models).
- **Gold card:** one per deck at most, for the single number the audience must remember. Gold fill with a Darkest Blue number.
- **Tables:** header row Darker Blue with white bold text, body Gray 80% on white with Gray 5% banding, numbers right-aligned, no vertical rules.
- **Source line:** every data slide carries a 9–10 pt Gray 60% note such as "Data: Kalshi course database, Oct 8–27 2026 · test period n = 2,299".

Do not use: accent lines under titles, colored bars along slide edges, gradients you make yourself, drop shadows, clip art, centered body text, or more than one gold card per slide.

**Speaker notes are required** on every slide, with a target time ("About 1:00"). A 15-minute slot is 12 minutes of talk plus 3 minutes of questions, so about 10–11 main slides. Backup slides go after the closing slide.

## 5. Plots

Use the helper. It sets every rule below:

```python
import sys; sys.path.insert(0, '../style_guide')
import ucla_style as us
us.apply()
fig, ax = us.figure('half')          # 'full' 9x4.2 in, 'half' 5.6x4.2, 'wide' 9x3.2, 'square' 5.2x4.6
ax.bar(x, y, color=us.PRIMARY)
us.label(ax, xi, yi, '5.7%')         # direct labels in text ink
us.save(fig, '../results/midterm/figures/name.png')   # 200 dpi PNG on white
```

1. **No title inside slide figures.** The slide title carries the message. Figures for the written report get a numbered caption in the document instead.
2. **Size for where it is shown.** Make the figure at the size it will appear (`figure('half')` for a half-slide) so that text sizes are true.
3. **Recessive frame:** no top or right spine, light horizontal grid only, no tick marks.
4. **Benchmark in gray, data in blue.** Show the comparison the claim depends on (price-implied rate, perfect-calibration line, zero line).
5. **Uncertainty:** 95% intervals as thin Darkest Blue error bars with small caps. Say in the note how they were computed ("event-level bootstrap", "Wilson").
6. **Direct labels beat legends.** With 2–4 series, label lines or bars directly; add a frameless legend only if labels would collide. A single series needs no legend.
7. **Numbers:** thousands separators (10,351), percentages to one decimal (4.96% where precision matters), cents as ¢, a true minus sign (−), units in axis labels.
8. **One axis.** Never two y-scales on one chart. Use two charts.
9. **Export** PNG at 200 dpi into `results/<phase>/figures/`, with file names in lowercase with underscores that describe the content (`loss_by_category.png`).

## 6. Writing

- Lead with the result and its number: "4.96% of test favorites lost vs 5.40% implied".
- Prefer plain words to jargon on slides; define a term the first time it appears ("Brier score: mean squared error of a probability").
- Name the comparison and the period for every number (test, validation, or all data).
- Hypothetical money results always say "one contract at the displayed ask, held to settlement, before fees".
- Never identify a trader or wallet (course rule).

## 7. Files

| File | What it is |
| --- | --- |
| `style_guide/STYLE_GUIDE.md` | This guide |
| `style_guide/ucla_style.py` | Plot palette and `apply()`, `figure()`, `label()`, `note()`, `save()` helpers |
| `style_guide/deck_theme.json` | Theme colors and fonts used by `slides/*/build_deck.js` |
| `slides/midterm/build_deck.js` | Reference implementation of the slide system |

## 8. Pre-flight checklist

- [ ] Every title states a finding, fits on one line, no period
- [ ] Only colors from section 2; gold never as text on white
- [ ] Every data slide has a source line; every chart a benchmark
- [ ] No text under 12 pt on slides (captions 9–11 pt)
- [ ] Figures made at display size with `ucla_style`
- [ ] Speaker notes with timings; total ≤ 12 minutes
- [ ] Team names spelled: Juan Cortes-Aguiar, Ravikiran Madichetty, Ashish Singh
- [ ] Rendered and checked slide by slide for overflow and overlaps

## Change log

| Date | Change |
| --- | --- |
| 2026-10-27 | Version 1.0: UCLA palette, Arial typography, slide system, plot rules |
