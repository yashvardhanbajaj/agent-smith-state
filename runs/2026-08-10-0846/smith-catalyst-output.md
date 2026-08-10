# Smith Catalyst Scan — 2026-08-10 (DEEP, pre-open)

## Asia session check (explicit ask): real catalyst or mechanical read-through?
Mostly momentum continuation, not a fresh discrete catalyst dated 08-10 itself.
KOSPI +5%, Nikkei 225 +~2% (1,155yen), led again by SK Hynix/Kioxia/SoftBank/Advantest/
Tokyo Electron. Traces back to a cluster of dated items already in the theme log:
Aug 4 SK Hynix+SanDisk HBF standard launch, Aug 4 SK Hynix ADR quiet-period expiry,
Aug 5 US tech/semis overnight rally read-through (SK Hynix +7%, Samsung +4%, Kioxia +7%),
and now Aug 7 SK Hynix's $38bn new-plant announcement. No single new named 08-10 trigger
found — this is compounding momentum in an already-running memory supercycle narrative,
not mechanical S&P-futures read-through and not a new fact set.

## New dated item this window (since 08-06 watermark)
SK Hynix confirmed $38bn investment in new memory chip plants (CNBC, 2026-08-07), citing
AI demand that has SK Hynix's 2026 capacity fully sold out already. Structural tailwind for
the memory cluster (SKHY, MU, DRAM) — new capacity targets future years, does not relieve
the near-term tightness that is the actual driver of current pricing and the Asia rally.

## CXMT / China semis (standing theme 1)
No new dated (within 08-06–08-10) development found. One capacity-comparison piece
(CXMT ~350k WPM vs Micron ~375k WPM DRAM capacity by end-2026, Morgan Stanley HBM
capacity estimate ~10k WPM by end-2026) surfaced but without a confirmable publish date
inside the window — withheld as a catalyst per the source+date hard rule. Existing 07-31
DUV-ceiling / 2027-timeline thread (LPDDR6 spec cap, back-end yield binding constraint)
stands unchanged.

## AI capex financing (standing theme 3)
No new dated development since 07-30 MSFT-beat de-escalation. Nvidia-OpenAI $250bn/$750bn
financing story and elevated Nvidia CDS levels are unchanged from the prior run — not
re-flagged as new.

## Memory pricing cross-check (HBMTracker read, required before any % claim)
Read /Users/yb/Claude/HBMTracker/consumer_view.json. No new corrections since C1/C2
(2026-08-05). HBM3/HBM3E flat on stack-derived basis (0.0% since 07-19); HBM4 +14.3% but
flagged suspect_band (basis-splice artifact per correction C2, not a clean move). No
percentage price claim is made in this run's catalysts — none of today's search results
produced a dated, sourced $/GB figure to check against the tracker.

## Policy & export controls (standing theme 5)
No new dated development found since the Jan 2026 H200-tariff/50%-cap rule already on
record. Quiet this week.

## Data quality notes
- TAIEX 08-10 move not found in snippets (Nikkei/KOSPI confirmed, TAIEX omitted from source).
- Cash % not in this run's inputs — exposure reported as % of equity only; book % assumed equal, flag if cash is elevated.
- CXMT capacity comparison piece intentionally excluded for lacking a confirmable date.

```json
{"catalysts":[
 {"headline":"SK Hynix to invest $38bn in new memory chip plants; 2026 capacity already fully sold out on AI demand","date":"2026-08-07","horizon":"structural","direction":"tailwind","affects":["SKHY","MU","DRAM"],"exposure_pct_equity":12.94,"exposure_pct_book":12.94,"magnitude":"New capacity is a multi-year build targeting 2027+ delivery; SK Hynix is already 100% sold out through 2026, so this does not relieve the near-term tightness driving current pricing/rally — capacity add, not a pivot.","source":"https://www.cnbc.com/2026/08/07/sk-hynix-memory-chips-ai-prices.html","invalidates_proposal":null},
 {"headline":"KOSPI +5%/Nikkei +2% Asia session, SK Hynix/Kioxia/SoftBank led — momentum continuation, not a fresh 08-10 catalyst","date":"2026-08-10","horizon":"immediate","direction":"tailwind","affects":["SKHY","MU","DRAM","TSM"],"exposure_pct_equity":18.41,"exposure_pct_book":18.41,"magnitude":"No new fact set for 08-10 itself; compounds Aug 4-7 items (HBF standard, SK Hynix ADR quiet-period end, $38bn capacity news) already reflected in prior sessions. Read as sentiment continuation, not incremental information — size conviction accordingly.","source":"https://www.tradingkey.com/analysis/stocks/more/262074716-japan-south-korea-stocks-rally-kospi-nikkei-softbank-sk-hynix-kioxia-tradingkey","invalidates_proposal":null}
],
 "asia_session":{"kospi_pct":5.0,"taiex_pct":null,"nikkei_pct":2.0,"named_cause":"Continuation of memory/AI-chip supercycle momentum (SK Hynix, Kioxia, SoftBank, Advantest, Tokyo Electron), reinforced by SK Hynix's 08-07 $38bn capacity announcement -- not a new discrete 08-10 catalyst"},
 "theme_updates":{"2":{"live_2026_08_10":"SK Hynix confirms $38bn new-plant investment (CNBC 08-07); 2026 capacity already fully sold out on AI/HBM demand. Tracker cross-check: no new corrections, HBM3/HBM3E flat and HBM4 move basis-flagged as of 08-05 -- no fresh $/GB figure to reconcile this run."},"6":{"live_2026_08_10":"KOSPI +5%, Nikkei +~2% -- momentum continuation of the memory rally, not a new named catalyst; TAIEX move not found this run."}},
 "searches_used":6,"data_quality":["TAIEX 08-10 move not found in search snippets","cash % not supplied this run -- exposure_pct_book assumed equal to exposure_pct_equity","CXMT capacity-comparison piece (Tom's Hardware/Morgan Stanley) withheld as a catalyst -- no confirmable in-window publish date"]}
```
