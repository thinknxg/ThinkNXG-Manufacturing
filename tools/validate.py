#!/usr/bin/env python3
import csv, json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(__file__))
import schema

CSV = sys.argv[1]
man = json.load(open(os.path.join(CSV, "..", "manifest.json")))
dtypes = {f["file"]: f["doctype"] for f in man["files"]}
problems, warns = [], []

# ---- collect package-defined names for link checks
def read(fn):
    with open(os.path.join(CSV, fn), encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]

names = collections.defaultdict(set)      # doctype -> names created by package
NAMEFIELD = {"Company": "company_name", "Item": "item_code", "Supplier": "supplier_name", "Customer": "customer_name",
             "Warehouse": None, "Account": None, "Cost Center": None, "UOM": "uom_name", "Item Group": "item_group_name",
             "Customer Group": "customer_group_name", "Supplier Group": "supplier_group_name", "Territory": "territory_name",
             "Workstation": "workstation_name", "Workstation Type": "workstation_type", "Operation": "name", "Fiscal Year": "year"}
AB = "KSSB"
for fn, dtp in dtypes.items():
    h, rows = read(fn)
    for r in rows:
        d = dict(zip(h, r))
        if dtp in ("Warehouse", ):
            if d.get("warehouse_name"): names[dtp].add(f"{d['warehouse_name']} - {AB}")
        elif dtp == "Account":
            names[dtp].add(f"{d['account_name']} - {AB}")
        elif dtp == "Cost Center":
            names[dtp].add(f"{d['cost_center_name']} - {AB}")
        elif NAMEFIELD.get(dtp) and d.get(NAMEFIELD[dtp]):
            names[dtp].add(d[NAMEFIELD[dtp]])
# BOM names
for fn, dtp in dtypes.items():
    if dtp == "BOM":
        h, rows = read(fn)
        for r in rows:
            d = dict(zip(h, r))
            if d.get("item"): names["BOM"].add(f"BOM-{d['item']}-001")
# defaults that ERPNext creates itself
BUILTIN = {
 "Warehouse": {f"{n} - {AB}" for n in ["All Warehouses", "Stores", "Work In Progress", "Finished Goods", "Goods In Transit"]},
 "Item Group": {"All Item Groups", "Raw Material", "Products", "Services", "Sub Assemblies", "Consumable"},
 "Customer Group": {"All Customer Groups"}, "Supplier Group": {"All Supplier Groups"}, "Territory": {"All Territories", "Rest Of The World"},
 "UOM": {"Kg", "Nos", "Meter", "Square Meter", "Litre", "Set", "Tonne"},
 "Price List": {"Standard Buying", "Standard Selling"}, "Currency": {"AED"}, "Country": {"United Arab Emirates", "Oman"},
 "Account": {f"{n} - {AB}" for n in ["Bank Accounts", "Direct Expenses", "Direct Income", "Temporary Opening", "Expenses Included In Valuation",
                                     "Freight and Forwarding Charges", "VAT 5%", "VAT Zero"]},
 "Cost Center": {f"Main - {AB}", f"KREATAO Structural Steel & Building Systems LLC - {AB}"},
 "Sales Taxes and Charges Template": {f"UAE VAT 5% - {AB}", f"UAE VAT Zero - {AB}"},
 "Purchase Taxes and Charges Template": {f"UAE VAT 5% - {AB}"},
 "Domain": {"Manufacturing"}, "Stock Entry Type": {"Manufacture"},
 "Mode of Payment": set(), "Supplier": set(), "Customer": set(),
}
DYN = {"Dynamic Link"}

def child_dt(parent_dt, table):
    f = schema.fields(parent_dt).get(table)
    return f["options"] if f and f["fieldtype"] in ("Table", "Table MultiSelect") else None

for fn, dtp in dtypes.items():
    h, rows = read(fn)
    pf = schema.fields(dtp)
    meta = schema.load(dtp)
    # --- header mapping
    colinfo = []
    for col in h:
        if "." in col:
            t, c = col.split(".", 1)
            cdt = child_dt(dtp, t)
            if not cdt: problems.append(f"{fn}: unknown table field '{t}'"); colinfo.append(None); continue
            cf = schema.fields(cdt)
            if c not in cf and c != "name": problems.append(f"{fn}: unknown child field {t}.{c} ({cdt})"); colinfo.append(None); continue
            colinfo.append((t, c, cf.get(c), cdt))
        else:
            if col not in pf and col != "name": problems.append(f"{fn}: unknown field '{col}' on {dtp}"); colinfo.append(None); continue
            colinfo.append((None, col, pf.get(col), dtp))
    # --- group rows into docs
    pidx = [i for i, ci in enumerate(colinfo) if ci and ci[0] is None]
    docs, cur = [], None
    for r in rows:
        if any(r[i] for i in pidx):
            cur = dict(parent=dict(zip(h, r)), kids=collections.defaultdict(list)); docs.append(cur)
        if cur is None: problems.append(f"{fn}: first row has no parent values"); break
        byt = collections.defaultdict(dict)
        for i, ci in enumerate(colinfo):
            if ci and ci[0] and r[i] != "": byt[ci[0]][ci[1]] = r[i]
        for t, v in byt.items(): cur["kids"][t].append(v)
    # --- mandatory columns / values
    for fname, f in pf.items():
        if f.get("reqd") and not f.get("hidden") and fname not in h and not f.get("default") and f["fieldtype"] not in ("Table",) and not f.get("fetch_from"):
            if fname in ("naming_series",) : problems.append(f"{fn}: mandatory column missing: {fname}")
            else: warns.append(f"{fn}: mandatory '{fname}' not supplied (no default in schema) - check")
    for d in docs:
        for fname, f in pf.items():
            if f.get("reqd") and fname in h and d["parent"].get(fname, "") == "" and f["fieldtype"] not in ("Check",):
                problems.append(f"{fn}: empty mandatory {fname} in doc {list(d['parent'].values())[:2]}")
        for t, rows_ in d["kids"].items():
            cdt = child_dt(dtp, t); cf = schema.fields(cdt)
            for cr in rows_:
                for cn, f in cf.items():
                    if f.get("reqd") and cn not in cr and not f.get("default") and not f.get("fetch_from") and cn in [ci[1] for ci in colinfo if ci and ci[0] == t]:
                        problems.append(f"{fn}: child {t}.{cn} empty mandatory")
    # --- select options & link checks
    for d in docs:
        for k, v in d["parent"].items():
            if v == "" or k == "name": continue
            f = pf.get(k)
            if not f: continue
            if f["fieldtype"] == "Select" and f.get("options"):
                opts = [o for o in f["options"].split("\n")]
                if v not in opts: problems.append(f"{fn}: {k}='{v}' not in {opts[:6]}...")
            if f["fieldtype"] == "Link":
                tgt = f["options"]
                if v not in names.get(tgt, set()) and v not in BUILTIN.get(tgt, set()):
                    warns.append(f"{fn}: external link {k} -> {tgt}:{v}")
        for t, rows_ in d["kids"].items():
            cdt = child_dt(dtp, t); cf = schema.fields(cdt)
            for cr in rows_:
                for k, v in cr.items():
                    f = cf.get(k)
                    if not f: continue
                    if f["fieldtype"] == "Select" and f.get("options") and v not in f["options"].split("\n"):
                        problems.append(f"{fn}: {t}.{k}='{v}' invalid select")
                    if f["fieldtype"] == "Link":
                        tgt = f["options"]
                        if tgt in ("DocType",): continue
                        if v not in names.get(tgt, set()) and v not in BUILTIN.get(tgt, set()):
                            warns.append(f"{fn}: external link {t}.{k} -> {tgt}:{v}")
    print(f"{fn:42s} {dtp:22s} docs={len(docs):3d} rows={len(rows):3d}")

# ---- unique-warn dedupe
seen = set()
print("\nPROBLEMS:", len(problems))
for p in problems: print("  !!", p)
print("\nWARNINGS (unique):")
for w in warns:
    key = w.split(": ", 1)[1]
    if key in seen: continue
    seen.add(key); print("  ~", w)
