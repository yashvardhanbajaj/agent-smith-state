# Factor Catalyst Scanner — 2026-07-28 13:35 ET (first dispatch, gap G30)

## Catalysts

**1. CXMT DDR5 pricing reality check — the panic's premise doesn't hold (structural / tailwind, relief for Memory cluster)**
CXMT's own retail-channel 64GB DDR5 server modules are pricing at 18,999 yuan vs 18,595 yuan for equivalent Samsung/SK Hynix modules — CXMT is **2.2% more expensive**, not undercutting. Damang2/Substack and MarketScreener both report CXMT has effectively abandoned the feared price war because its production cost still runs >30% above the Korean incumbents. CXMT holds 8% global DRAM share vs Samsung 36% / SK Hynix 29% / Micron 24%. The market priced a price war on IPO-day momentum (+400-531%); the first hard pricing data says the opposite is happening.
Affects: MU, SNDK, EWY, DRAM (Memory/Storage cluster) — 19.41% equity / 10.16% book.
Source: https://www.digitaltoday.co.kr/en/view/85083/cxmt-server-ddr5-pricier-than-samsung-sk-hynix ; https://www.marketscreener.com/news/chinaa-s-cxmt-abandons-price-war-ce7f5edadf88f524 (2026-07-27/28)

**2. Nvidia $250bn OpenAI guarantee — the leverage ratio nobody had sized yet (structural / threat)**
Nvidia's own FY27 Q1 10-Q caps total disclosed lease-guarantee exposure at $3.5bn. A $250bn Ohio-campus commitment would run **~71x** that disclosed cap. Michael Burry's "around and around we go" framing (Nvidia guaranteeing OpenAI's spend on Nvidia's own chips) is now the dominant sell-side lens, not a fringe short-seller take — this is the number that sharpens "circular financing" from a slogan into a specific, checkable red flag. NVDA -5% Mon 7/27 on the report.
Affects (financing-structure theme, not NVDA itself which is unheld): AVGO, AMD, ORCL, GOOG — 28.38% equity / 14.85% book.
Source: https://www.techtimes.com/articles/321652/20260727/nvidias-250b-guarantee-openai-ohio-campus-proves-debt-markets-said-no.htm (2026-07-27)

**3. Alphabet's own capex raise, not just Nvidia's, is now a live source of hyperscaler-cluster anxiety (structural / ambiguous)**
Q2 (reported 2026-07-22): Google raised FY26 capex guidance to $195-205bn (from $180-190bn), quarterly capex $44.9bn drove **quarterly FCF negative -$5.9bn** despite a revenue beat (+24% YoY, cloud +82%). GOOGL fell ~6-7% on the print even with the beat. CNBC (2026-07-28) reports Amazon/Meta/Microsoft now face the same skeptical framing into their prints this week — the read-through risk is to the whole Hyperscaler cluster, not just GOOG. Tailwind side: capex raise = more AI infra spend = demand support for AVGO/optics/memory suppliers; threat side: the market is now pricing capex-intensity against near-term FCF, and GOOG is the book's single largest position.
Affects: GOOG directly — 14.02% equity / 7.34% book (Hyperscaler cluster 16.42%/8.60% incl. ORCL).
Source: https://www.cnbc.com/2026/07/22/google-earnings-q2-goog-live-updates.html ; https://www.cnbc.com/2026/07/28/hyperscalers-face-higher-capex-scrutiny-after-alphabet-report-panned.html

**4. Asia session — 8th circuit breaker of the year, cause chain fully confirmed (immediate, already re-priced)**
KOSPI's -10.2/-10.84% trip was the Korea Exchange's **8th circuit breaker in 2026**, confirming this is a recurring fragility pattern, not a one-off. Named cause is the same three-part chain already known this morning (CXMT debut, DUV mass-production, Nvidia/OpenAI financing) transmitted via overnight US semi weakness — no new cause found, only confirmation and the "8th time" frequency data point.
Affects: EWY, TSM, MU, SNDK, DRAM — 29.96% equity / 15.68% book.
Source: https://finance.biggo.com/news/91abffd1-38bf-47a0-b147-e8e0206ff75c (2026-07-28)

## invalidates_proposal
Neither open proposal (NVDA re-entry, CEG new position) is invalidated. Catalyst #2 raises the bar for diligence on the NVDA thesis before Thu 7/30 (financing-structure scrutiny, not a stop/technical issue) but does not undermine the stated rationale (mis-calibrated stop + relative strength). Flagging as a live risk, not a kill.

## Data quality
Asia index levels taken as given by orchestrator, not re-verified. CXMT pricing is a single retail-channel data point (not official contract pricing) — directional signal, not a confirmed contract-price trend.

```json
{"catalysts":[
{"headline":"CXMT DDR5 server modules pricing 2.2% ABOVE Samsung/SK Hynix — feared price war not materializing, CXMT cost base >30% higher","date":"2026-07-27","horizon":"structural","direction":"tailwind","affects":["MU","SNDK","EWY","DRAM"],"exposure_pct_equity":19.41,"exposure_pct_book":10.16,"magnitude":"CXMT 8% DRAM share vs Samsung 36%/SK Hynix 29%/Micron 24%; priced 2.2% above incumbents, not below","source":"https://www.digitaltoday.co.kr/en/view/85083/cxmt-server-ddr5-pricier-than-samsung-sk-hynix","invalidates_proposal":null},
{"headline":"Nvidia $250bn OpenAI guarantee = ~71x its own disclosed lease-guarantee cap ($3.5bn), sharpening circular-financing scrutiny","date":"2026-07-27","horizon":"structural","direction":"threat","affects":["AVGO","AMD","ORCL","GOOG"],"exposure_pct_equity":28.38,"exposure_pct_book":14.85,"magnitude":"$250bn commitment vs $3.5bn disclosed 10-Q guarantee cap = ~71x leverage on that cap","source":"https://www.techtimes.com/articles/321652/20260727/nvidias-250b-guarantee-openai-ohio-campus-proves-debt-markets-said-no.htm","invalidates_proposal":null},
{"headline":"Alphabet raised FY26 capex to $195-205bn, quarterly FCF went negative -$5.9bn; Amazon/Meta/Microsoft now face same skepticism into this week's prints","date":"2026-07-22","horizon":"structural","direction":"ambiguous","affects":["GOOG"],"exposure_pct_equity":14.02,"exposure_pct_book":7.34,"magnitude":"capex guide +8% at midpoint ($185bn to $200bn mid); Q2 capex $44.9bn vs quarterly FCF -$5.9bn; revenue still beat +24% YoY, cloud +82%","source":"https://www.cnbc.com/2026/07/22/google-earnings-q2-goog-live-updates.html","invalidates_proposal":null},
{"headline":"KOSPI's 2026-07-28 plunge was the Korea Exchange's 8th circuit breaker this year — confirms recurring fragility, cause chain unchanged from this morning","date":"2026-07-28","horizon":"immediate","direction":"threat","affects":["EWY","TSM","MU","SNDK","DRAM"],"exposure_pct_equity":29.96,"exposure_pct_book":15.68,"magnitude":"8th circuit breaker of 2026; KOSPI -34% in 25 trading days after a prior +300% spike","source":"https://finance.biggo.com/news/91abffd1-38bf-47a0-b147-e8e0206ff75c","invalidates_proposal":null}
],
"asia_session":{"kospi_pct":-10.84,"taiex_pct":-4.65,"nikkei_pct":-3.95,"named_cause":"CXMT +400% Shanghai debut + China DUV mass-production start + Nvidia/OpenAI $250bn circular-financing scrutiny, transmitted via overnight US semi weakness (SMH -3.08%); 8th KOSPI circuit breaker of 2026"},
"theme_updates":{},
"searches_used":6,
"data_quality":["Asia index levels taken as given by orchestrator, not independently re-verified","CXMT pricing is a single retail-channel data point, not confirmed contract pricing"]}
```
