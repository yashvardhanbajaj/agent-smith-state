import json

usdinr = 96.555  # reused from last run (19:07), refresher mode doesn't refetch FX

qty = {
"NVDA":12,"STM":10,"VRT":5,"AMD":2,"EWY":10,"DRAM":50,"ORCL":4,"CIEN":1.388528082,
"TER":3.002730188,"ARM":2,"BABA":5,"CLS":5.003266352,"GLW":10,"TSM":6,"ASML":1.000001151,
"GEV":1.394950742,"IREN":25,"QCOM":14.000761904,"LRCX":5,"COHR":3,"NBIS":6,"MU":2.000365376,
"LITE":1,"AVGO":2,"SNDK":3.008131251,"AMAT":0.0091785,"MRVL":7,"GOOG":2
}

names = {
"NVDA":"NVIDIA Corporation Common Stock","STM":"STMicroelectronics N.V.","VRT":"Vertiv Holdings Co Class A Common Stock",
"AMD":"Advanced Micro Devices, Inc. Common Stock","EWY":"iShares MSCI South Korea ETF","DRAM":"Roundhill Memory ETF",
"ORCL":"Oracle Corp","CIEN":"Ciena Corporation","TER":"Teradyne, Inc. Common Stock","ARM":"Arm Holdings plc American Depositary Shares",
"BABA":"Alibaba Group Holding Limited American Depositary Shares","CLS":"Celestica, Inc.","GLW":"Corning Incorporated",
"TSM":"Taiwan Semiconductor Manufacturing Company Ltd.","ASML":"ASML Holding N.V. New York Registry Shares",
"GEV":"GE Vernova Inc.","IREN":"IREN Limited Ordinary Shares","QCOM":"QUALCOMM Incorporated Common Stock",
"LRCX":"Lam Research Corporation Common Stock","COHR":"Coherent Corp.","NBIS":"Nebius Group N.V. Class A Ordinary Shares",
"MU":"Micron Technology, Inc. Common Stock","LITE":"Lumentum Holdings Inc. Common Stock","AVGO":"Broadcom Inc. Common Stock",
"SNDK":"Sandisk Corporation Common Stock","AMAT":"Applied Materials, Inc. Common Stock","MRVL":"Marvell Technology, Inc. Common Stock",
"GOOG":"Alphabet Inc. Class C Capital Stock"
}

mkt_cap = {
"NVDA":"Mega Cap","STM":"Large Cap","VRT":"Large Cap","AMD":"Mega Cap","EWY":"Mid Cap","DRAM":"",
"ORCL":"Mega Cap","CIEN":"Mid Cap","TER":"Large Cap","ARM":"Large Cap","BABA":"Mega Cap","CLS":"Mid Cap",
"GLW":"Large Cap","TSM":"Mega Cap","ASML":"Mega Cap","GEV":"Large Cap","IREN":"Small Cap","QCOM":"Large Cap",
"LRCX":"Large Cap","COHR":"Large Cap","NBIS":"","MU":"Large Cap","LITE":"Mid Cap","AVGO":"Large Cap",
"SNDK":"","AMAT":"Large Cap","MRVL":"Large Cap","GOOG":"Mega Cap"
}

# invested_amount from indmoney fetch (INR), for pnl_pct calc
invested_inr = {
"NVDA":227294.19695630725,"STM":59206.17916296387,"VRT":139848.81646309508,"AMD":97468.65525959624,
"EWY":171761.8015910927,"DRAM":290900.6974128311,"ORCL":48312.591806710814,"CIEN":53572.15725975037,
"TER":99363.37150135027,"ARM":51857.50472442627,"BABA":56691.021483226774,"CLS":150828.55389769154,
"GLW":151984.85421405945,"TSM":248342.13391247083,"ASML":172400.90268519724,"GEV":142213.93698886366,
"IREN":87818.83505960084,"QCOM":241445.9943495891,"LRCX":161316.12307909774,"COHR":83385.35618362426,
"NBIS":109768.9637843399,"MU":172131.15864363473,"LITE":70743.96825138092,"AVGO":76171.65934533539,
"SNDK":454000.6177981481,"AMAT":495.0425146438522,"MRVL":140653.52684771604,"GOOG":66259.74634711914
}

indmoney_mv_inr = {
"NVDA":232185.1345709106,"STM":68118.55506413267,"VRT":154538.1948430941,"AMD":104333.30927973613,
"EWY":176283.8374519348,"DRAM":307053.5287145234,"ORCL":55044.44980245363,"CIEN":61255.37198655159,
"TER":103932.59720457612,"ARM":62569.07271946408,"BABA":53023.50632425689,"CLS":169371.68189461651,
"GLW":183564.19761712663,"TSM":250161.78870906355,"ASML":172157.22858448946,"GEV":143120.02889688686,
"IREN":99520.45891319285,"QCOM":255307.24124857536,"LRCX":168493.00470904564,"COHR":93673.26860013418,
"NBIS":123775.58360746759,"MU":189274.20066248986,"LITE":74976.21347640082,"AVGO":76545.8267475646,
"SNDK":533376.2216765763,"AMAT":515.5422556685012,"MRVL":162485.51514516154,"GOOG":67983.06092812493
}

yf_usd = {
"NVDA":212.06,"STM":65.77,"VRT":301.16,"AMD":552.33,"EWY":170.43,"DRAM":57.77,"ORCL":125.84,
"CIEN":397.16,"TER":369.46,"ARM":283.4,"BABA":116.56,"CLS":335.5,"GLW":154.06,"TSM":421.21,
"ASML":1801.86,"GEV":985.03,"IREN":41.28,"QCOM":175.63,"LRCX":319.29,"COHR":312.19,"NBIS":218.16,
"MU":959.48,"LITE":829.7,"AVGO":396.81,"SNDK":1599.27,"AMAT":553.92,"MRVL":210.99,"GOOG":341.91
}

rows = []
divergences = []
total_yf_inr = 0
total_indmoney_inr = 0
for t in qty:
    yf_mv_inr = qty[t]*yf_usd[t]*usdinr
    im_mv = indmoney_mv_inr[t]
    div_pct = (im_mv - yf_mv_inr)/yf_mv_inr*100
    total_yf_inr += yf_mv_inr
    total_indmoney_inr += im_mv
    if abs(div_pct) > 3:
        divergences.append((t, round(div_pct,2)))
    rows.append({
        "ticker": t, "name": names[t], "qty": qty[t],
        "market_value_inr": round(yf_mv_inr,4),
        "invested_inr": round(invested_inr[t],4),
        "pnl_pct": round((yf_mv_inr-invested_inr[t])/invested_inr[t]*100,4),
        "market_cap": mkt_cap[t],
    })

total = sum(r["market_value_inr"] for r in rows)
for r in rows:
    r["weight_pct"] = round(r["market_value_inr"]/total*100,6)

print("Total (yfinance-priced):", round(total,2), "INR ->", round(total/usdinr,2), "USD")
print("Total (INDmoney feed):", round(total_indmoney_inr,2), "INR ->", round(total_indmoney_inr/usdinr,2), "USD")
print("Divergence total pct:", round((total_indmoney_inr-total_yf_inr)/total_yf_inr*100,2))
print()
print("Names diverging >3% (INDmoney vs yfinance):", len(divergences))
for t,d in sorted(divergences, key=lambda x:-abs(x[1])):
    print(f"  {t}: {d:+.2f}%")

out = {
    "ts": "2026-07-23T20:15:00+05:30",
    "usdinr": usdinr,
    "source": "REFRESHER MODE: qty from fresh networth_holdings(US_STOCK) call; price from yfinance direct quotes (INDmoney feed re-checked and again diverging >3% on multiple names post-G22, same-day recurrence -- discarded again, see reconciliation_note)",
    "market_session": "intraday",
    "holdings_inr": rows
}
json.dump(out, open("/Users/yb/Claude/AgentSmith/runs/2026-07-23-refresh/holdings.json","w"), indent=2)
