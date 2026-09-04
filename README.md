# in-west-capital

**Reappraise** — a single-file appraisal sheet for French residential property. Open it, enter a deal, and it tells you
whether the numbers survive — including the two things that usually decide it: how wrong the build cost
can be before the deal dies, and what the tax regime does to the profit.

No build step, no dependencies, no server, no analytics. One `index.html`. Data stays in your browser.

## What it does

**Models the deal twice.** Exit A renovates and sells; Exit B renovates and lets. Same acquisition, same
leverage, two very different answers — a project can clear a 30 % resale margin and still be unable to
service its own debt as a rental.

**Prices the French specifics rather than approximating them.**

- *Frais de notaire* computed on the vendor price, with buyer-borne agency fees excluded from the DMTO
  base — the correct treatment when the fee is *à la charge de l'acquéreur*
- DMTO presets: 5.80665 %, 6.32 % (départements at the 5.00 % cap), 0.715 % (marchand de biens)
- Works quoted HT with TVA at 5.5 / 10 / 20 %, so the *immeuble neuf* risk is a visible lever
- Resale TVA: none, *sur marge* at 20 %, or 20 % on the full price with input TVA recovered
- Plus-value for a private individual: 19 % IR + 17.2 % PS with the statutory abattement schedule
  (IR exempt at 22 years, PS at 30) plus the surtaxe brackets
- *Marchand de biens* / SCI à l'IS: 15 % to 42 500 € then 25 %
- Exit A prices the **loi Carrez** area, which is not the habitable area

**Finds the edges.** Break-even build cost per m², break-even exit price per m², and a stress case
(works cost up, exit price down, rate up) that has to stay profitable before the verdict reads INVEST.
A deal that only works at the base case gets CONDITIONAL, which is the honest answer.

**Checks the file, not just the maths.** A 30-item French due-diligence checklist — servitudes,
pre-emption rights, *permis de diviser*, ABF, DPE exemptions, CREP and asbestos by build year,
drainage and lift pumps, the géomètre's Carrez certificate, TVA position in writing. Progress is
tracked per property and appears in the comparison table, because a deal with great numbers and 4/30
checks done is not a deal yet.

**Compares properties side by side.** Unlimited properties, saved in `localStorage`, with a comparison
table and CSV export. JSON export/import to move a portfolio between machines or hand it to someone else.

**Reconciles the unit schedule.** Per-unit areas and rents drive the rental case, the total is checked
against the declared surface, and any unit under 9 m² is flagged — French *décence* rules will not accept
it as a lettable room, and in a colocation the rule applies per tenant.

## Use it

Open `index.html` in a browser. That is the whole installation.

To host it: push to GitHub, then **Settings → Pages → Source: GitHub Actions**. The included workflow
publishes it on every push to `main`.

The Nantes example (a 275 m² 1850 *hôtel particulier* for division into six dwellings) loads on first
run so you can see the shape of a filled-in sheet. Delete it or keep it as a reference.

## What it will not do

It will not tell you whether dividing into lots defeats *TVA sur marge*, whether your works cross the
*immeuble neuf* threshold, or whether a flip gets requalified as BIC. Those are legal judgements about
your specific facts and they need a notaire and a fiscaliste. The tool makes the size of each question
visible so you know which ones are worth paying to answer.

Rates and thresholds are hard-coded as of **September 2026**. Check them before you rely on a number:
DMTO rates change by département and by year, and the *encadrement des loyers* map keeps moving.

## Licence

MIT. See [LICENSE](LICENSE).
