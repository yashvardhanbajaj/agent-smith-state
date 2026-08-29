import json

USDINR = 95.38

holdings = [
 ("GE Vernova Inc.", 261603.17892758964, 3.004950742, 6.848148514571678),
 ("Bloom Energy Corporation", 160969.2614880614, 8, 4.213792100960248),
 ("Amkor Technology, Inc. Common Stock", 49393.590707572876, 10, 1.2930066301948635),
 ("Super Micro Computer, Inc. Common Stock", 36715.83671754459, 10, 0.9611332083548773),
 ("Nebius Group N.V. Class A Ordinary Shares", 104285.95996015938, 5, 2.729958193625484),
 ("QUALCOMM Incorporated Common Stock", 109732.72825902962, 7.000761904, 2.872541622420319),
 ("Broadcom Inc. Common Stock", 70413.07363038324, 2, 1.8432466591768952),
 ("Amazon.com, Inc. Common Stock", 152608.4296505861, 6, 3.994925425245125),
 ("Celestica, Inc.", 60696.328165009116, 2.003266352, 1.5888853922459942),
 ("Teradyne, Inc. Common Stock", 67866.93818692217, 2.002730188, 1.7765948939861422),
 ("NVIDIA Corporation Common Stock", 103842.05122322077, 5, 2.718337719555049),
 ("ASML Holding N.V. New York Registry Shares", 165632.91487174455, 1.000001151, 4.335875445370933),
 ("SK hynix Inc. American Depositary Shares", 77140.49058216857, 5, 2.019354421300172),
 ("Advanced Micro Devices, Inc. Common Stock", 88893.18342623301, 2, 2.3270119443174084),
 ("Taiwan Semiconductor Manufacturing Company Ltd.", 122376.57530950941, 3, 3.2035274412936494),
 ("Western Digital Corporation Common Stock", 88209.65661621094, 2, 2.3091188394709334),
 ("Lam Research Corporation Common Stock", 115283.52724694833, 4, 3.0178483270239473),
 ("Coherent Corp.", 106615.31257153302, 4, 2.790935100293378),
 ("Lumentum Holdings Inc. Common Stock", 85441.17172241211, 1, 2.2366464949420837),
 ("Marvell Technology, Inc. Common Stock", 186116.6433651857, 9, 4.872090698680512),
 ("Vertiv Holdings Co Class A Common Stock", 171794.97983666416, 7, 4.497183638219342),
 ("IREN Limited Ordinary Shares", 77383.92370080575, 20, 2.0257269208876263),
 ("Franklin FTSE Taiwan ETF", 99350.42139750673, 10, 2.600757542413992),
 ("Microsoft Corporation Common Stock", 96431.1016346924, 2, 2.524336700055611),
 ("Micron Technology, Inc. Common Stock", 133615.7513612922, 1.500365376, 3.4977423170438025),
 ("Corning Incorporated", 113778.99797238782, 8, 2.978463331937313),
 ("STMicroelectronics N.V.", 147035.1877966232, 30, 3.8490312198305614),
 ("Ciena Corporation", 114840.56931686423, 3.008528082, 3.0062527428137003),
 ("Blackstone Inc.", 135932.60770285036, 10, 3.5583921011135486),
 ("KLA Corporation Common Stock", 67031.69926485606, 4, 1.7547303271758026),
 ("Alphabet Inc. Class C Capital Stock", 130932.15364189446, 4, 3.4274921166787355),
 ("Intel Corporation Common Stock", 128118.8000832824, 15, 3.353845217308652),
 ("Applied Materials, Inc. Common Stock", 88507.1059802309, 2.0081785, 2.316905355784397),
 ("Constellation Energy Corporation Common Stock", 79259.81320953369, 3, 2.0748332429337037),
 ("Alibaba Group Holding Limited American Depositary Shares, each represents eight Ordinary Shares", 22207.06698198244, 2, 0.5813281527735218),
]

tm = json.load(open('/Users/yb/Claude/AgentSmith/state.json')).get('data_cache',{}).get('ticker_map',{})

def resolve(name):
    if name in tm:
        return tm[name]
    # try stripping trailing " Common Stock"
    for suffix in [" Common Stock", ", Common Stock"]:
        if name.endswith(suffix):
            base = name[: -len(suffix)]
            if base in tm:
                return tm[base]
    # substring match
    for k, v in tm.items():
        if k in name or name in k:
            return v
    return None

rows = []
new_resolutions = []
for name, mv_inr, qty, wt in holdings:
    tk = resolve(name)
    if tk is None:
        new_resolutions.append(name)
        tk = "UNRESOLVED:" + name
    rows.append({"ticker": tk, "name": name, "qty": qty, "market_value_inr": mv_inr, "weight_pct": wt})

print("NEW RESOLUTIONS NEEDED:", new_resolutions)
out = {
    "usdinr": USDINR,
    "holdings_inr": rows,
    "market_session": "closed_weekend",
}
json.dump(out, open('/Users/yb/Claude/AgentSmith/runs/2026-08-29-0816/holdings_partial.json','w'), indent=2)
print("wrote", len(rows), "rows")
