// Builds slides/midterm/Almost_Certain_Midterm.pptx following style_guide/STYLE_GUIDE.md.
// Run from the repo root:  node slides/midterm/build_deck.js
// Optional: set PPTX_SKILL to a folder containing scripts/apply_theme.js to also write the theme colors into the file.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.join(__dirname, "..", "..");
const FIG = path.join(ROOT, "results", "midterm", "figures");
const OUT = path.join(__dirname, "Almost_Certain_Midterm.pptx");
const THEME = JSON.parse(fs.readFileSync(path.join(ROOT, "style_guide", "deck_theme.json"), "utf8"));
const applyTheme = process.env.PPTX_SKILL ? require(process.env.PPTX_SKILL + "/scripts/apply_theme.js").applyTheme : async () => {};

// ---- style guide tokens (section 2) ----
const K = {
  blue: "2774AE", gold: "FFD100", white: "FFFFFF", darkerBlue: "005587", darkestBlue: "003B5C",
  lighterBlue: "8BB8E8", lightestBlue: "DAEBFE", darkestGold: "FFB81C",
  ink: "333333", ink2: "666666", gray5: "F2F2F2",
};
const FONT = "Arial";
const TEAM = "Juan Cortes-Aguiar  ·  Ravikiran Madichetty  ·  Ashish Singh";
const SOURCE = "Data: Kalshi course database, hourly candles Oct 8–27, 2026";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "The 99-Cent Question: How Accurate Are Kalshi’s Odds? STATS 414 midterm";
pres.author = "Juan Cortes-Aguiar, Ravikiran Madichetty, Ashish Singh";
pres.company = "UCLA STATS 414";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

// ---- layouts (section 4) ----
pres.defineSlideMaster({
  title: "BLUE",
  background: { color: K.blue },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.55, w: 8.8, h: 0.95, fontSize: 42, bold: true, color: K.white, fontFace: FONT, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.65, w: 8.8, h: 2.3, fontSize: 18, color: K.white, fontFace: FONT, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: K.white },
  margin: [0.5, 0.5, 0.5, 0.5],
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.5, y: 0.22, w: 9.0, h: 0.25, fontSize: 11, bold: true, color: K.blue, fontFace: FONT, charSpacing: 1, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.47, w: 9.0, h: 0.55, fontSize: 26, bold: true, color: K.darkerBlue, fontFace: FONT, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "STATS 414  ·  The 99-Cent Question", options: { x: 0.5, y: 5.27, w: 5, h: 0.22, fontSize: 9, color: K.ink2, fontFace: FONT, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.27, w: 0.5, h: 0.22, fontSize: 9, color: K.ink2, fontFace: FONT, align: "right" },
});

// ---- helpers ----
function pngAspect(file) { const b = fs.readFileSync(file); return b.readUInt32BE(16) / b.readUInt32BE(20); }
function fig(s, name, x, y, w, maxH) {
  const f = path.join(FIG, name); const a = pngAspect(f);
  let width = w, h = w / a;
  if (maxH && h > maxH) { h = maxH; width = h * a; }
  s.addImage({ path: f, x, y, w: width, h, objectName: name, altText: name.replace(/_/g, " ").replace(".png", "") });
  return { w: width, h };
}
const txt = (s, text, o) => s.addText(text, Object.assign({ fontFace: FONT, color: K.ink, margin: 0, valign: "top", isTextBox: true }, o));
function stat(s, x, y, w, big, small, color) {
  txt(s, big, { x, y, w, h: 0.6, fontSize: 34, bold: true, color: color || K.blue });
  txt(s, small, { x, y: y + 0.62, w, h: 0.45, fontSize: 12, color: K.ink2 });
}
function goldCard(s, x, y, w, h, big, small, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: K.gold }, line: { color: K.gold }, objectName: name });
  txt(s, big, { x: x + 0.2, y: y + 0.14, w: w - 0.4, h: 0.6, fontSize: 34, bold: true, color: K.darkestBlue });
  txt(s, small, { x: x + 0.2, y: y + 0.76, w: w - 0.4, h: h - 0.86, fontSize: 12, color: K.darkestBlue });
}
function card(s, x, y, w, h, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: K.lightestBlue }, line: { color: K.lightestBlue }, objectName: name });
}
function bullets(s, items, x, y, w, h, size) {
  txt(s, items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1 } })),
    { x, y, w, h, fontSize: size || 14, paraSpaceAfter: 6 });
}
const source = (s, text) => txt(s, text, { x: 0.5, y: 4.95, w: 9.0, h: 0.22, fontSize: 9, color: K.ink2 });
function content(kicker, title, section) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(kicker.toUpperCase(), { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  return s;
}
function table(s, rows, o) {
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
    bold: i === 0, color: i === 0 ? K.white : K.ink, fill: { color: i === 0 ? K.darkerBlue : (i % 2 ? K.white : K.gray5) },
    align: j ? "right" : "left", fontFace: FONT } }))), Object.assign({ border: { type: "none" }, valign: "middle" }, o));
}

// Timing plan (speaker notes): 12 main slides ≈ 10:20 of talk, leaving about 4:40 for questions in the 15-minute slot.

// ================= 1 · title =================
pres.addSection({ title: "Question" });
let s = pres.addSlide({ masterName: "BLUE", sectionTitle: "Question" });
s.addText("The 99-Cent Question: How Accurate Are Kalshi’s Odds?", { placeholder: "title" });
s.addText([
  { text: "What 7 million hourly prices say about Kalshi, and whether 90–99¢ favorites are as safe as they look", options: { breakLine: true } },
  { text: " ", options: { breakLine: true, fontSize: 12 } },
  { text: "STATS 414 MIDTERM  ·  OCTOBER 28, 2026", options: { fontSize: 14, bold: true, color: K.gold, charSpacing: 1, breakLine: true } },
  { text: TEAM, options: { fontSize: 14 } },
], { placeholder: "body" });
s.addNotes("About 0:30. We explored every hourly price on Kalshi for three weeks of October, then zoomed in on contracts priced 90 to 99 cents, the near-sure things, to see whether they are as safe as their price says.");

// ================= 2 · questions =================
s = content("Roadmap", "Three questions about Kalshi prices", "Question");
[["1", "What does Kalshi trade?", "Markets, volume and liquidity across 840,000 markets"],
 ["2", "Are its prices right?", "Calibration across 1–99¢, then a zoom on 90–99¢ favorites"],
 ["3", "Can a model beat the price?", "Logistic, random forest and XGBoost vs the quoted price"]].forEach(([n, h, d], i) => {
  const x = 0.5 + i * 3.05; card(s, x, 1.2, 2.8, 2.0, "q-" + n);
  txt(s, n, { x: x + 0.2, y: 1.3, w: 0.6, h: 0.6, fontSize: 32, bold: true, color: K.blue });
  txt(s, h, { x: x + 0.2, y: 1.95, w: 2.4, h: 0.5, fontSize: 15, bold: true, color: K.darkerBlue });
  txt(s, d, { x: x + 0.2, y: 2.45, w: 2.4, h: 0.7, fontSize: 12 });
});
txt(s, [{ text: "Why favorites?  ", options: { bold: true, color: K.blue } },
  { text: "A YES contract pays $1 or $0, so its price is the crowd's probability. Buying at 99¢ risks 99¢ to make 1¢: one loss wipes out 99 wins. Whether that is a good bet depends entirely on how accurate the price is." }],
  { x: 0.5, y: 3.5, w: 9, h: 1.2, fontSize: 14 });
s.addNotes("About 0:45. Three questions. First, what is actually traded on Kalshi. Second, are prices accurate, first across the whole range, then for favorites. Third, can a model predict which favorites lose better than the price already does. Favorites matter because the payoff is so lopsided: one loss at 99 cents erases 99 wins.");

// ================= 3 · data =================
pres.addSection({ title: "Data" });
s = content("Data", "Every hourly Kalshi price for three weeks, with gaps", "Data");
stat(s, 0.5, 1.2, 2.0, "7.17M", "hourly candles (bid, ask, volume), Oct 8–27");
stat(s, 0.5, 2.35, 2.0, "839,613", "markets in 67,261 events");
fig(s, "coverage_by_day.png", 3.2, 1.15, 6.3, 3.7);
source(s, SOURCE + "  ·  hours with at least one candle per UTC day");
s.addNotes("About 1:00. We pulled every hourly candle in the course database, 7.17 million rows covering 840 thousand markets, before access closes on Thursday. One thing EDA showed immediately: the record has holes. Some days have 24 hours, others one or none. And many rows were backfilled after the market closed. So everything we show is a retrospective look, not what a trader saw live.");

// ================= 4 · landscape =================
pres.addSection({ title: "Exploration" });
s = content("Exploration 1", "Sports and crypto are most of Kalshi", "Exploration");
fig(s, "eda_landscape.png", 0.5, 1.1, 5.9, 3.75);
stat(s, 6.65, 1.2, 2.85, "76%", "of contracts traded were Sports, from 37% of markets");
bullets(s, [
  "The top 1% of markets carry 82% of all volume",
  "72% of markets never traded in the window",
  "Politics, Economics, Tech and Entertainment: each under 0.4% of volume",
], 6.65, 2.4, 2.85, 2.4, 12);
source(s, SOURCE + "  ·  volume = contracts traded, summed over hourly candles");
s.addNotes("About 1:00. Blue is share of contracts traded, gray is share of markets listed. Sports is three quarters of all trading; crypto is listed heavily but trades less. Trading is extremely concentrated: one percent of markets carry 82% of the volume, and most markets never trade at all. The categories our final project is about are a sliver of volume, which matters later.");

// ================= 5 · prices & spreads =================
s = content("Exploration 2", "Most quotes are long shots; spreads peak at 50¢", "Exploration");
fig(s, "eda_prices_spreads.png", 0.5, 1.1, 9.0, 3.05);
bullets(s, [
  "Left: 21% of hourly quotes are below 10¢ and 5.5% above 90¢, because events list one market per outcome",
  "Right: the median spread is 4¢ overall, 1–2¢ at the extremes and widest near 50¢, where outcomes are least certain",
], 0.5, 4.2, 9.0, 0.7, 12);
source(s, SOURCE + "  ·  5.5M valid two-sided quotes (0 < bid ≤ ask < 1)");
s.addNotes("About 0:50. Left, where prices sit: most quotes are cheap long shots, because an event like 'who wins' lists one market per candidate. Right, how wide the bid-ask spread is: tight at the extremes, widest at 50 cents where uncertainty is highest. Also, 89% of hourly candles have zero volume, so volume is mostly zeros, a hint for why it will not help our models.");

// ================= 6 · calibration full range =================
s = content("Exploration 3", "Prices are calibrated except at the extremes", "Exploration");
fig(s, "eda_calibration_full_range.png", 0.5, 1.1, 5.2, 3.75);
stat(s, 6.0, 1.2, 3.5, "0.5 pts", "average gap between win rate and price, 129,866 markets");
bullets(s, [
  "Long shots under 2¢ won 0.8% of the time vs 1.6% priced; 2–5¢ won 2.5% vs 3.5%",
  "95–100¢ favorites won 1 point more often than priced",
  "Gold: long shots overpriced; blue: favorites underpriced",
], 6.0, 2.4, 3.5, 2.4, 12);
source(s, SOURCE + "  ·  first quote per finalized market (spread ≤ 5¢)  ·  95% Wilson intervals");
s.addNotes("About 1:10. We took every finalized market's first quote and compared the price with how often it actually won. Plotted as a gap, prices are within half a point on average. But at the ends there is the classic favorite–long-shot bias: cheap long shots win less often than their price, and heavy favorites win slightly more often. That makes favorites look like a possible edge, so we zoom in on them next.");

// ================= 7 · favorites by category =================
pres.addSection({ title: "Favorites" });
s = content("Favorites", "Economics favorites were underpriced", "Favorites");
fig(s, "loss_by_category.png", 0.5, 1.1, 6.0, 3.75);
txt(s, [
  { text: "10,351 favorites, 513 lost", options: { bold: true, color: K.darkerBlue, breakLine: true } },
  { text: "First quote per market with ask 90–99¢, midpoint ≥ 90¢, spread ≤ 5¢", options: { breakLine: true } },
  { text: " ", options: { breakLine: true, fontSize: 8 } },
  { text: "Economics", options: { bold: true, color: K.darkerBlue, breakLine: true } },
  { text: "0.5% lost vs 3.5% implied; 95% CI of the gap [−3.4, −2.6] pts; held in every period; mostly AAA gas-price markets", options: { breakLine: true } },
  { text: " ", options: { breakLine: true, fontSize: 8 } },
  { text: "Financials 7.3% vs 4.8%, but its CI includes 0" },
], { x: 6.75, y: 1.2, w: 2.75, h: 3.6, fontSize: 12 });
source(s, SOURCE + "  ·  intervals resample whole events (1,000 bootstrap draws)");
s.addNotes("About 1:00. Now only the favorites: 10,351 markets whose first good quote was 90 to 99 cents, 513 of which lost. By category, most sit at their implied loss rate, the dark tick. Economics is the exception: 7 losses where the price implied about 53. Markets in one event move together, so we bootstrapped whole events; the interval still excludes zero, and it held in all three time periods.");

// ================= 8 · favorites by time to event =================
s = content("Favorites", "Favorites lose as priced until the event starts", "Favorites");
fig(s, "loss_by_time_to_event.png", 0.5, 1.1, 5.6, 3.75);
bullets(s, [
  "From 1 hour to 3 days out, loss rates match the price",
  "At or after the scheduled event start: 2.7–3.2% lost vs about 5% implied",
  "A small effect, and not stable across periods",
], 6.4, 1.25, 3.1, 3.6, 12);
source(s, SOURCE + "  ·  time from entry to the scheduled event time  ·  all periods, n = 10,351");
s.addNotes("About 0:40. Splitting favorites by how far away the event was: they lose about as often as priced, except right at or after the start, where they lose less. The effect is small and moves around between periods, so we treat it as a feature for the models rather than a finding.");

// ================= 9 · method =================
pres.addSection({ title: "Models" });
s = content("Models", "We split by date and tuned three model families", "Models");
[["Train", "Entries Oct 9–11", "4,358 markets · 179 losses"], ["Validation", "Entries Oct 15–18", "3,694 markets · 220 losses"], ["Test", "Entries Oct 20–25", "2,299 markets · 114 losses"]].forEach(([n, d, m], i) => {
  const x = 0.5 + i * 3.05; card(s, x, 1.2, 2.8, 1.25, "split-" + n);
  txt(s, n, { x: x + 0.2, y: 1.28, w: 2.4, h: 0.36, fontSize: 17, bold: true, color: K.darkerBlue });
  txt(s, d, { x: x + 0.2, y: 1.66, w: 2.4, h: 0.26, fontSize: 12, color: K.ink2 });
  txt(s, m, { x: x + 0.2, y: 1.98, w: 2.4, h: 0.3, fontSize: 13, bold: true });
});
txt(s, "Features at entry", { x: 0.5, y: 2.7, w: 4.3, h: 0.3, fontSize: 14, bold: true, color: K.darkerBlue });
bullets(s, ["Price, spread, open interest", "Volume now and in the prior 6 h", "Hours to the scheduled event; recent price change", "Category; markets in the event"], 0.5, 3.05, 4.3, 1.8, 12);
txt(s, "Models (tuned on validation Brier)", { x: 5.2, y: 2.7, w: 4.3, h: 0.3, fontSize: 14, bold: true, color: K.darkerBlue });
bullets(s, ["Elastic-net logistic (Week 3): C = 0.01, L1 share 0.5", "Random forest (Week 4): depth 4", "XGBoost (Week 4): depth 2, learning rate 0.03", "Each with and without volume; baseline = the quoted price"], 5.2, 3.05, 4.3, 1.8, 12);
s.addNotes("About 1:00. We split by time, the way a forecaster would face it, and kept every event inside one split so related markets cannot leak across. Features are all known at the entry hour. We tuned three course models on the validation period by Brier score, the mean squared error of a probability, refit on train plus validation, and scored the test period once. Every model is fit with and without volume to isolate what volume adds.");

// ================= 10 · results =================
s = content("Models", "No model beat the quoted price", "Models");
fig(s, "model_vs_price.png", 0.5, 1.1, 5.9, 3.75);
stat(s, 6.65, 1.2, 2.85, "0.04624", "test Brier score of the quoted price: the best of all");
bullets(s, [
  "Closest: elastic net, 0.04629 (gap CI −0.00015 to +0.00025)",
  "Volume changed Brier by at most 0.0001 in every family",
  "The elastic net set every volume, timing and category coefficient to 0",
], 6.65, 2.4, 2.85, 2.4, 12);
source(s, "Data: Kalshi course database, Oct 8–27, 2026  ·  test n = 2,299  ·  event-bootstrap 95% CIs  ·  gray: CI includes 0, gold: worse");
s.addNotes("About 1:00. Each dot is a model's test Brier minus the price's; left of zero would beat the price, and none do clearly. The regularized logistic regression essentially ties the price, because it shrank everything except price-like features to zero. The tree models fit training data better and test data worse: bias versus variance. Consistent with the EDA, volume adds nothing.");

// ================= 11 · economics =================
s = content("Models", "Buying every favorite at the ask still lost money", "Models");
fig(s, "economics_by_split.png", 0.5, 1.1, 5.2, 3.75);
goldCard(s, 6.0, 1.2, 3.5, 1.4, "−$19.61", "on 2,299 test contracts, even though 95.0% of them won", "gold-card");
bullets(s, [
  "Per contract: −0.85¢ in test, −2.16¢ in validation, +0.25¢ in train",
  "The small favorite edge from slide 6 does not survive buying at the ask",
], 6.0, 2.85, 3.5, 1.9, 12);
source(s, "Data: Kalshi course database, Oct 8–27, 2026  ·  one contract at the displayed ask, held to settlement, before fees");
s.addNotes("About 0:40. If you bought one contract of every test favorite at the ask and held it, 95% would win and you would still be down about 20 dollars before fees. Buying at the ask rather than the midpoint eats the small favorite edge we saw in the calibration plot, and the result flips sign between periods.");

// ================= 12 · close =================
pres.addSection({ title: "Close" });
s = pres.addSlide({ masterName: "BLUE", sectionTitle: "Close" });
s.addText("What we learned", { placeholder: "title" });
s.addText([
  { text: "Kalshi is mostly sports and crypto, and most markets barely trade", options: { bullet: { indent: 16 }, breakLine: true } },
  { text: "Prices are calibrated within half a point, with a favorite–long-shot bias at the ends", options: { bullet: { indent: 16 }, breakLine: true } },
  { text: "No model beat the price for favorites, and buying them at the ask lost money", options: { bullet: { indent: 16 } } },
], { placeholder: "body" });
s.addNotes("About 0:45. Three takeaways: what Kalshi trades, how accurate its prices are, and that favorites are not free money. For the final we look at the other end of the calibration plot: long shots that won, and whether informed trading shows up before the news. Then questions. Total talk is about 10:20, leaving four to five minutes for questions.");

// ================= 13 · thank you =================
s = pres.addSlide({ masterName: "BLUE", sectionTitle: "Close" });
s.addText("Thank you", { placeholder: "title" });
s.addText([
  { text: "Questions?", options: { fontSize: 24, bold: true, color: K.gold, breakLine: true } },
  { text: " ", options: { breakLine: true, fontSize: 12 } },
  { text: TEAM, options: { fontSize: 14, breakLine: true } },
  { text: "STATS 414  ·  UCLA  ·  Fall 2026", options: { fontSize: 12 } },
], { placeholder: "body" });
s.addNotes("Thank the class and open the floor for questions (about 4 to 5 minutes remain in the 15-minute slot).");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
