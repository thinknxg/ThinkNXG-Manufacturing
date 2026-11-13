#!/usr/bin/env python3
"""
KREATAO UAE Structural Steel & Building Systems - ERPNext v16 demo dataset generator.
Produces numbered Data-Import-ready CSV files (headers are v16 fieldnames; child tables use
`table.fieldname`, which the v16 Data Import column matcher accepts).
All parties, products and transactions are fictional.
"""
import csv, os, sys, json, re, datetime as dt
from collections import defaultdict, OrderedDict

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/out/csv"
os.makedirs(OUT, exist_ok=True)

CO = "KREATAO Structural Steel & Building Systems LLC"
AB = "KSSB"
def a(name): return f"{name} - {AB}"          # account / warehouse / cost-centre naming
WH_YARD, WH_STORES, WH_WIP, WH_FG = a("Steel Yard"), a("Stores"), a("Work In Progress"), a("Finished Goods")
WH_DISP, WH_SCRAP, WH_QC = a("Dispatch Yard"), a("Scrap & Offcuts"), a("Quarantine & Rejected")
CC = a("Main")
VAT, VAT0 = a("VAT 5%"), a("VAT Zero")
T_VAT, T_VAT0 = a("UAE VAT 5%"), a("UAE VAT Zero")

FILES = []   # (filename, doctype, rows, submit, note)

# --------------------------------------------------------------------------- writer
def fmt(v):
    if isinstance(v, bool): return 1 if v else 0
    if isinstance(v, float):
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s
    return v

_COUNTER = [0]
def write(fname, doctype, docs, submit=False, note=""):
    """docs: list of dict; list-valued keys are child tables (key = table fieldname)."""
    base = re.sub(r"^\d\d_", "", fname)
    fname = f"{_COUNTER[0]:02d}_{base}"; _COUNTER[0] += 1
    pcols, ccols = [], OrderedDict()
    for d in docs:
        for k, v in d.items():
            if isinstance(v, list):
                for row in v:
                    for ck in row:
                        ccols.setdefault(k, [])
                        if ck not in ccols[k]: ccols[k].append(ck)
            elif k not in pcols:
                pcols.append(k)
    header = pcols + [f"{t}.{c}" for t, cs in ccols.items() for c in cs]
    path = os.path.join(OUT, fname)
    nrows = 0
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        for d in docs:
            kids = {t: d.get(t, []) for t in ccols}
            n = max([1] + [len(v) for v in kids.values()])
            for i in range(n):
                row = []
                for p in pcols:
                    row.append(fmt(d.get(p, "")) if i == 0 else "")
                for t, cs in ccols.items():
                    ch = kids[t][i] if i < len(kids[t]) else {}
                    row += [fmt(ch.get(c, "")) for c in cs]
                w.writerow(row); nrows += 1
    FILES.append(dict(file=fname, doctype=doctype, docs=len(docs), rows=nrows, submit=submit, note=note))

D = lambda s: dt.date.fromisoformat(s)
def iso(d): return d.isoformat()
def plus(s, n): return iso(D(s) + dt.timedelta(days=n))

# =========================================================================== MASTER DATA
# 00 Fiscal year (optional prerequisite)
write("00_prereq_Fiscal_Year_2026.csv", "Fiscal Year",
      [dict(year="2026", year_start_date="2026-01-01", year_end_date="2026-12-31",
            companies=[dict(company=CO)])],
      note="OPTIONAL - skip if Fiscal Year 2026 already exists (ERPNext setup normally creates it).")

# 01 Company
write("01_Company.csv", "Company", [dict(
    company_name=CO, abbr=AB, default_currency="AED", country="United Arab Emirates",
    create_chart_of_accounts_based_on="Standard Template", chart_of_accounts="Standard",
    domain="Manufacturing", tax_id="100000000000003", date_of_establishment="2018-03-01",
    enable_perpetual_inventory=1)],
    note="Creating the Company auto-creates the chart of accounts, warehouses (Stores, Work In Progress, "
         "Finished Goods, Goods In Transit), Main cost centre and the 'UAE VAT 5%' / 'UAE VAT Zero' tax templates.")

# 02 Accounts
write("02_Account.csv", "Account", [
    dict(account_name="Emirates NBD Current Account (Demo)", parent_account=a("Bank Accounts"), company=CO, account_type="Bank", is_group=0),
    dict(account_name="Mashreq Collection Account (Demo)", parent_account=a("Bank Accounts"), company=CO, account_type="Bank", is_group=0),
    dict(account_name="Galvanizing Subcontract Charges", parent_account=a("Direct Expenses"), company=CO, is_group=0),
    dict(account_name="Steel Scrap Sales", parent_account=a("Direct Income"), company=CO, account_type="Income Account", is_group=0),
])

# 03 Cost centres
ROOT_CC = f"{CO} - {AB}"
CCS = ["Structural Steel Fabrication", "Building Systems (PEB)", "Roofing & Cladding", "Projects & Erection"]
write("03_Cost_Center.csv", "Cost Center",
      [dict(cost_center_name=c, parent_cost_center=ROOT_CC, company=CO, is_group=0) for c in CCS])
CC_STRUCT, CC_PEB, CC_ROOF, CC_PROJ = [a(c) for c in CCS]

# 04 Warehouses
write("04_Warehouse.csv", "Warehouse", [
    dict(warehouse_name="Steel Yard", parent_warehouse=a("All Warehouses"), company=CO, is_group=0, city="Sharjah"),
    dict(warehouse_name="Dispatch Yard", parent_warehouse=a("All Warehouses"), company=CO, is_group=0, city="Sharjah"),
    dict(warehouse_name="Scrap & Offcuts", parent_warehouse=a("All Warehouses"), company=CO, is_group=0, city="Sharjah"),
    dict(warehouse_name="Quarantine & Rejected", parent_warehouse=a("All Warehouses"), company=CO, is_group=0, city="Sharjah"),
], note="Stores / Work In Progress / Finished Goods / Goods In Transit already exist after Company creation.")

# 05 UOM
write("05_UOM.csv", "UOM", [
    dict(uom_name="Sheet", must_be_whole_number=1, enabled=1),
    dict(uom_name="Bundle", must_be_whole_number=1, enabled=1),
], note="Kg, Nos, Meter, Square Meter, Litre, Set, Tonne already ship with ERPNext.")

# 06 Item groups
IG = [("Structural Sections", "Raw Material"), ("Steel Plates & Flats", "Raw Material"),
      ("Cold Formed & Coil", "Raw Material"), ("Fasteners & Anchors", "Raw Material"),
      ("Welding Consumables", "Raw Material"), ("Paint & Coatings", "Raw Material"),
      ("Workshop Consumables", "Raw Material"),
      ("Structural Steel Members", "Products"), ("Pre-Engineered Building Components", "Products"),
      ("Platforms & Staircases", "Products"), ("Roofing & Cladding Systems", "Products")]
write("06_Item_Group.csv", "Item Group",
      [dict(item_group_name=n, parent_item_group=p, is_group=0) for n, p in IG],
      note="Raw Material / Products / Services / Sub Assemblies / Consumable are ERPNext defaults.")

# 07-09 Customer group / supplier group / territory
write("07_Customer_Group.csv", "Customer Group", [
    dict(customer_group_name=n, parent_customer_group="All Customer Groups", is_group=0)
    for n in ["Contractors & EPC", "Developers", "Industrial & Manufacturing", "Government & Municipal"]])
write("08_Supplier_Group.csv", "Supplier Group", [
    dict(supplier_group_name=n, parent_supplier_group="All Supplier Groups", is_group=0)
    for n in ["Steel Mills & Traders", "Welding & Gases", "Paints & Coatings Suppliers",
              "Fasteners & Hardware Suppliers", "Subcontract & Logistics"]])
EMIRATES = ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain", "Export - GCC"]
write("09_Territory.csv", "Territory", [
    dict(territory_name=n, parent_territory="All Territories", is_group=0) for n in EMIRATES])

# 10-12 Operations / workstation types / workstations
WS = OrderedDict([  # name -> (type, AED/hour)
    ("CNC Plasma Cutting Line", ("CNC Cutting", 180)),
    ("Beam Drilling & Punching Line", ("Drilling & Punching", 150)),
    ("Roll Forming Line", ("Roll Forming", 130)),
    ("Fit-Up Bay 1", ("Fabrication Bay", 90)),
    ("Welding Bay 1", ("Welding Bay", 110)),
    ("Welding Bay 2", ("Welding Bay", 110)),
    ("Shot Blasting Booth", ("Surface Treatment", 140)),
    ("Paint Booth 1", ("Surface Treatment", 120)),
    ("Final Assembly Yard", ("Fabrication Bay", 80)),
    ("QC Inspection Bench", ("Quality Control", 70)),
])
OPS = OrderedDict([  # operation -> (default workstation, description)
    ("Cutting & Profiling", ("CNC Plasma Cutting Line", "Plasma/oxy profile cutting of plates and section cut-to-length")),
    ("Drilling & Punching", ("Beam Drilling & Punching Line", "Bolt-hole drilling and punching per shop drawing")),
    ("Roll Forming", ("Roll Forming Line", "Roll forming of trapezoidal roofing/cladding profile")),
    ("Fit-Up", ("Fit-Up Bay 1", "Assembly, alignment and tack welding")),
    ("Welding", ("Welding Bay 1", "Full/partial penetration and fillet welding (MIG/SAW)")),
    ("Shot Blasting", ("Shot Blasting Booth", "Abrasive blast cleaning to Sa 2.5")),
    ("Painting", ("Paint Booth 1", "Primer / intermediate / finish coat application and DFT check")),
    ("Final Assembly", ("Final Assembly Yard", "Match-marking, bolting of sub-assemblies, packing")),
    ("Quality Inspection", ("QC Inspection Bench", "Dimensional, weld visual / NDT and coating inspection")),
])
write("10_Workstation_Type.csv", "Workstation Type",
      [dict(workstation_type=t, description=f"{t} (demo)") for t in OrderedDict.fromkeys(v[0] for v in WS.values())])
COMPONENTS = [("Electricity & Utilities", 0.15), ("Machine Running & Depreciation", 0.45), ("Direct Labour", 0.40)]
write("11_Workstation_Operating_Component.csv", "Workstation Operating Component",
      [dict(component_name=c) for c, _p in COMPONENTS])
write("11_Workstation.csv", "Workstation", [
    dict(workstation_name=n, workstation_type=t, production_capacity=1,
         workstation_costs=[dict(operating_component=c, operating_cost=round(r * p, 2)) for c, p in COMPONENTS],
         description=f"{n} - KREATAO Sharjah workshop (demo)",
         working_hours=[dict(start_time="07:00:00", end_time="12:00:00", enabled=1),
                        dict(start_time="13:00:00", end_time="17:30:00", enabled=1)])
    for n, (t, r) in WS.items()])

write("12_Operation.csv", "Operation",
      [dict(name=n, workstation=w, description=d) for n, (w, d) in OPS.items()],
      note="Operation uses 'Prompt' naming: the 'name' (ID) column sets the operation name. Imported after the workstations it points to.")

# =========================================================================== ITEMS
# code: (name, group, uom, rate, wt/unit kg, default wh, description)
RM = OrderedDict([
    ("RM-HB-300",  ("H-Beam HB300x150 Hot Rolled S355", "Structural Sections", "Kg", 3.35, 1.0, WH_YARD, "Hot rolled H-section 300x150, grade S355JR")),
    ("RM-IPE-200", ("IPE 200 Beam S275", "Structural Sections", "Kg", 3.30, 1.0, WH_YARD, "IPE200 European beam, grade S275JR")),
    ("RM-UB-406",  ("Universal Beam UB406x178x54 S355", "Structural Sections", "Kg", 3.40, 1.0, WH_YARD, "UB 406x178x54 kg/m, grade S355JR")),
    ("RM-UC-203",  ("Universal Column UC203x203x46 S355", "Structural Sections", "Kg", 3.40, 1.0, WH_YARD, "UC 203x203x46 kg/m, grade S355JR")),
    ("RM-PFC-150", ("Parallel Flange Channel PFC150x75 S275", "Structural Sections", "Kg", 3.25, 1.0, WH_YARD, "PFC 150x75 channel")),
    ("RM-ANG-75",  ("Equal Angle 75x75x6 S275", "Structural Sections", "Kg", 3.20, 1.0, WH_YARD, "Equal angle L75x75x6")),
    ("RM-RHS-100", ("RHS 100x50x4 Hollow Section S355", "Structural Sections", "Kg", 3.65, 1.0, WH_YARD, "Rectangular hollow section 100x50x4")),
    ("RM-PL-06",   ("MS Plate 6 mm (Chequered) S275", "Steel Plates & Flats", "Kg", 3.15, 1.0, WH_YARD, "6 mm chequered plate, 2.5 x 6 m")),
    ("RM-PL-10",   ("MS Plate 10 mm S355", "Steel Plates & Flats", "Kg", 3.15, 1.0, WH_YARD, "10 mm plate, 2.5 x 12 m")),
    ("RM-PL-16",   ("MS Plate 16 mm S355", "Steel Plates & Flats", "Kg", 3.20, 1.0, WH_YARD, "16 mm plate, 2.5 x 12 m")),
    ("RM-PL-20",   ("MS Plate 20 mm S355", "Steel Plates & Flats", "Kg", 3.20, 1.0, WH_YARD, "20 mm plate, 2.5 x 12 m")),
    ("RM-FB-50",   ("Flat Bar 50x10 S275", "Steel Plates & Flats", "Kg", 3.10, 1.0, WH_YARD, "Flat bar 50 x 10 mm")),
    ("RM-ZP-200",  ("Z Purlin 200x2.0 Cold Formed (Coil Cut Length)", "Cold Formed & Coil", "Meter", 20.90, 5.8, WH_YARD, "Z200x2.0 mm cold formed purlin, ~5.8 kg/m")),
    ("RM-PPGL-05", ("Pre-Painted Galvalume Coil 0.50 mm AZ150", "Cold Formed & Coil", "Kg", 4.90, 1.0, WH_YARD, "PPGL coil 0.50 mm, 1,220 mm width")),
    ("RM-BOLT-M20", ("HSFG Bolt M20x70 Gr 8.8 with Nut & Washer", "Fasteners & Anchors", "Nos", 3.80, 0.32, WH_STORES, "M20x70 high strength bolt assembly")),
    ("RM-BOLT-M16", ("Structural Bolt M16x50 Gr 8.8 with Nut & Washer", "Fasteners & Anchors", "Nos", 1.60, 0.16, WH_STORES, "M16x50 bolt assembly")),
    ("RM-ANCH-M24", ("Anchor Bolt M24x600 Gr 5.8 with Nuts", "Fasteners & Anchors", "Nos", 14.50, 2.1, WH_STORES, "M24x600 L-type anchor bolt")),
    ("RM-SCR-TEK", ("Self Drilling Roofing Screw 5.5x38", "Fasteners & Anchors", "Nos", 0.12, 0.01, WH_STORES, "Self drilling screw with EPDM washer")),
    ("RM-WIRE-ER70", ("MIG Welding Wire ER70S-6 1.2 mm (15 kg spool)", "Welding Consumables", "Kg", 8.20, 1.0, WH_STORES, "Copper coated solid wire 1.2 mm")),
    ("RM-ELEC-7018", ("Welding Electrode E7018 3.2 mm", "Welding Consumables", "Kg", 9.50, 1.0, WH_STORES, "Low hydrogen electrode 3.2 mm")),
    ("RM-GAS-MIX", ("Shielding Gas Ar/CO2 Mix 20 Cylinder", "Welding Consumables", "Nos", 140.00, 0, WH_STORES, "Argon 82% / CO2 18% cylinder (exchange)")),
    ("RM-PRIMER-ZP", ("Zinc Phosphate Primer (20 L)", "Paint & Coatings", "Litre", 22.00, 0, WH_STORES, "2-pack epoxy zinc phosphate primer")),
    ("RM-EPOXY-INT", ("Epoxy Intermediate Coat MIO", "Paint & Coatings", "Litre", 31.00, 0, WH_STORES, "Micaceous iron oxide epoxy build coat")),
    ("RM-PU-FIN", ("Polyurethane Finish Coat RAL 7035", "Paint & Coatings", "Litre", 38.00, 0, WH_STORES, "Aliphatic PU finish")),
    ("RM-THINNER", ("Epoxy Thinner", "Paint & Coatings", "Litre", 9.00, 0, WH_STORES, "Thinner for epoxy / PU")),
    ("RM-GRIT-G25", ("Steel Grit G25 Abrasive", "Workshop Consumables", "Kg", 1.10, 1.0, WH_STORES, "Blast abrasive grit G25")),
    ("CN-DISC-125", ("Grinding Disc 125 mm", "Workshop Consumables", "Nos", 6.50, 0.2, WH_STORES, "125 x 6 mm grinding disc")),
])
UNUSED = {"CN-DISC-125"}   # kept as pure stock/consumable item, not in any BOM

SERV = OrderedDict([  # services: (name, uom, buy, sell, desc)
    ("SRV-ERECT",    ("Steel Erection & Installation (per Tonne)", "Tonne", 0, 780.00, "Site erection, bolting and alignment")),
    ("SRV-GALV",     ("Hot-Dip Galvanizing - Subcontract (per Kg)", "Kg", 1.45, 0, "Subcontracted galvanizing to ISO 1461")),
    ("SRV-DETAIL",   ("Shop Drawing & Detailing (per Drawing)", "Nos", 0, 120.00, "Shop drawing / fabrication detailing")),
    ("SRV-TRANSPORT", ("Transport & Delivery (per Trip)", "Nos", 650.00, 850.00, "Low-bed / flat-bed delivery within UAE")),
])

# ----------------------------------------------------------------- BOM definitions
# item: (name, group, uom, kind, weight kg/unit, default wh, [(component, qty)], [(operation, minutes)], margin)
SA = OrderedDict([
    ("SA-BASEPLATE", ("Column Base Plate Assembly 400x400x20", "Nos", [("RM-PL-20", 25.2), ("RM-PL-10", 2.0), ("RM-WIRE-ER70", 0.15)],
                      [("Cutting & Profiling", 12), ("Fit-Up", 10), ("Welding", 15)], 29.0)),
    ("SA-ENDPLATE", ("Rafter End Plate Assembly 250x500x16", "Nos", [("RM-PL-16", 16.5), ("RM-WIRE-ER70", 0.10)],
                     [("Cutting & Profiling", 10), ("Drilling & Punching", 8)], 17.0)),
    ("SA-STRINGER", ("Stair Stringer Pair PFC150 (Standard)", "Set", [("RM-PFC-150", 143.0), ("RM-PL-06", 12.0), ("RM-WIRE-ER70", 0.40)],
                     [("Cutting & Profiling", 25), ("Fit-Up", 30), ("Welding", 35)], 156.0)),
])
FG = OrderedDict([  # item: (name, group, uom, mode, weight, comps, ops, margin%, cc, reorder(level, qty) or None)
    ("FG-PURLIN-Z200", ("Z Purlin 200x2.0 Punched 6 m", "Roofing & Cladding Systems", "Nos", "MTS", 34.8,
                        [("RM-ZP-200", 6.0)], [("Drilling & Punching", 4)], 24, CC_ROOF, (150, 400))),
    ("FG-ROOF-TR-05", ("Trapezoidal Roofing Sheet PPGL 0.50 mm (per m2)", "Roofing & Cladding Systems", "Square Meter", "MTS", 4.25,
                       [("RM-PPGL-05", 4.25)], [("Roll Forming", 2.5)], 26, CC_ROOF, (800, 2000))),
    ("FG-STAIR-STD", ("Industrial Steel Staircase 1.2 m x 3 m Rise (Standard)", "Platforms & Staircases", "Nos", "MTS", 330.0,
                      [("SA-STRINGER", 1.0), ("RM-PL-06", 85.0), ("RM-ANG-75", 22.0), ("RM-FB-50", 14.0), ("RM-BOLT-M16", 16.0),
                       ("RM-WIRE-ER70", 1.2), ("RM-PRIMER-ZP", 3.0), ("RM-EPOXY-INT", 2.0)],
                      [("Fit-Up", 90), ("Welding", 120), ("Painting", 60), ("Final Assembly", 45), ("Quality Inspection", 20)], 25, CC_STRUCT, (4, 10))),
    ("FG-PEB-FRAME-30", ("PEB Main Frame 30 m Span Portal (Column + Rafter Set)", "Pre-Engineered Building Components", "Nos", "MTO", 3300.0,
                         [("RM-HB-300", 3055.0), ("SA-BASEPLATE", 2.0), ("SA-ENDPLATE", 4.0), ("RM-PL-10", 60.0), ("RM-BOLT-M20", 32.0),
                          ("RM-ANCH-M24", 8.0), ("RM-WIRE-ER70", 14.0), ("RM-PRIMER-ZP", 22.0), ("RM-THINNER", 2.0), ("RM-GRIT-G25", 60.0)],
                         [("Cutting & Profiling", 90), ("Drilling & Punching", 60), ("Fit-Up", 150), ("Welding", 240),
                          ("Shot Blasting", 75), ("Painting", 90), ("Quality Inspection", 30)], 21, CC_PEB, None)),
    ("FG-MEZZ-BEAM-12", ("Mezzanine Main Beam UB406 12 m (Fabricated)", "Structural Steel Members", "Nos", "MTO", 720.0,
                         [("RM-UB-406", 648.0), ("SA-ENDPLATE", 2.0), ("RM-PL-10", 20.0), ("RM-BOLT-M20", 8.0), ("RM-WIRE-ER70", 3.0),
                          ("RM-PRIMER-ZP", 6.0), ("RM-GRIT-G25", 15.0)],
                         [("Cutting & Profiling", 40), ("Drilling & Punching", 30), ("Fit-Up", 60), ("Welding", 90),
                          ("Shot Blasting", 35), ("Painting", 40), ("Quality Inspection", 15)], 20, CC_STRUCT, None)),
    ("FG-ROOF-TRUSS-24", ("Roof Truss 24 m Span (Fabricated)", "Structural Steel Members", "Nos", "MTO", 840.0,
                          [("RM-RHS-100", 408.0), ("RM-ANG-75", 130.0), ("RM-PL-10", 45.0), ("SA-ENDPLATE", 2.0), ("RM-BOLT-M16", 24.0),
                           ("RM-WIRE-ER70", 7.0), ("RM-PRIMER-ZP", 8.0), ("RM-GRIT-G25", 30.0)],
                          [("Cutting & Profiling", 80), ("Fit-Up", 180), ("Welding", 260), ("Shot Blasting", 60),
                           ("Painting", 80), ("Final Assembly", 60), ("Quality Inspection", 25)], 22, CC_STRUCT, None)),
    ("FG-CRANE-GIRDER-10T", ("Crane Runway Girder 10 T Capacity 10 m", "Structural Steel Members", "Nos", "MTO", 880.0,
                             [("RM-UB-406", 540.0), ("RM-PL-16", 180.0), ("RM-PL-10", 55.0), ("SA-ENDPLATE", 2.0), ("RM-BOLT-M20", 12.0),
                              ("RM-WIRE-ER70", 9.0), ("RM-PRIMER-ZP", 8.0), ("RM-EPOXY-INT", 8.0), ("RM-PU-FIN", 6.0), ("RM-GRIT-G25", 25.0)],
                             [("Cutting & Profiling", 70), ("Drilling & Punching", 40), ("Fit-Up", 150), ("Welding", 300),
                              ("Shot Blasting", 70), ("Painting", 120), ("Quality Inspection", 45)], 23, CC_STRUCT, None)),
    ("FG-PIPE-RACK-6M", ("Pipe Rack Module 6 m Bay (Fabricated)", "Structural Steel Members", "Nos", "MTO", 1860.0,
                         [("RM-UC-203", 920.0), ("RM-IPE-200", 806.0), ("RM-ANG-75", 90.0), ("SA-BASEPLATE", 4.0), ("RM-BOLT-M20", 24.0),
                          ("RM-WIRE-ER70", 10.0), ("RM-PRIMER-ZP", 12.0), ("RM-EPOXY-INT", 8.0), ("RM-GRIT-G25", 45.0)],
                         [("Cutting & Profiling", 100), ("Drilling & Punching", 60), ("Fit-Up", 200), ("Welding", 280),
                          ("Shot Blasting", 90), ("Painting", 100), ("Final Assembly", 60), ("Quality Inspection", 30)], 21, CC_STRUCT, None)),
    ("FG-PLAT-ACCESS", ("Access Platform with Handrail & Chequered Plate", "Platforms & Staircases", "Nos", "MTO", 420.0,
                        [("RM-PFC-150", 160.0), ("RM-ANG-75", 60.0), ("RM-PL-06", 120.0), ("RM-BOLT-M16", 20.0), ("RM-WIRE-ER70", 3.0),
                         ("RM-PRIMER-ZP", 5.0), ("RM-EPOXY-INT", 3.0)],
                        [("Cutting & Profiling", 45), ("Fit-Up", 80), ("Welding", 100), ("Painting", 50), ("Final Assembly", 40), ("Quality Inspection", 15)], 24, CC_STRUCT, None)),
])
OVERHEAD_PCT = 0.0   # conversion cost is operation cost only; keep BOM cost == RM + operating cost

# ---- BOM costing (bottom-up) -------------------------------------------------
rate = {c: v[3] for c, v in RM.items()}
BOMCOST = {}
def op_cost(ops):
    return sum(mins / 60.0 * WS[OPS[o][0]][1] for o, mins in ops)
def cost_of(code):
    if code in BOMCOST: return BOMCOST[code]
    spec = SA.get(code) or FG.get(code)
    comps, ops = (spec[2], spec[3]) if code in SA else (spec[5], spec[6])
    rm = sum(q * (rate[c] if c in rate else cost_of(c)) for c, q in comps)
    tot = rm + op_cost(ops)
    qty = 1.0
    BOMCOST[code] = round(tot / qty, 2)
    for c, q in comps:
        pass
    return BOMCOST[code]
for k in list(SA) + list(FG): cost_of(k)
rate.update({k: BOMCOST[k] for k in BOMCOST})
SELL = {}
for k, v in SA.items(): SELL[k] = None
for k, v in FG.items():
    SELL[k] = round(BOMCOST[k] * (1 + v[7] / 100.0), 0) if v[2] != "Square Meter" else round(BOMCOST[k] * (1 + v[7] / 100.0), 2)
    if k == "FG-PURLIN-Z200": SELL[k] = round(BOMCOST[k] * 1.24, 2)

def item_defaults(wh): return [dict(company=CO, default_warehouse=wh)]
items = []
for c, (n, g, u, r, wt, wh, desc) in RM.items():
    d = dict(item_code=c, item_name=n, item_group=g, stock_uom=u, is_stock_item=1, is_purchase_item=1, is_sales_item=0,
             include_item_in_manufacturing=1, valuation_rate=r, description=desc,
             default_material_request_type="Purchase", item_defaults=item_defaults(wh))
    if wt: d.update(weight_per_unit=wt, weight_uom="Kg")
    if c not in UNUSED and wh == WH_YARD:
        d["reorder_levels"] = [dict(warehouse=WH_YARD, warehouse_reorder_level=2000 if u != "Meter" else 800,
                                    warehouse_reorder_qty=6000 if u != "Meter" else 2000, material_request_type="Purchase")]
    items.append(d)
for c, (n, u, buy, sell, desc) in SERV.items():
    items.append(dict(item_code=c, item_name=n, item_group="Services", stock_uom=u, is_stock_item=0,
                      is_purchase_item=1 if buy else 0, is_sales_item=1 if sell else 0, include_item_in_manufacturing=0,
                      description=desc, standard_rate=sell or 0, item_defaults=item_defaults(WH_STORES)))
for c, (n, u, comps, ops, wt) in SA.items():
    items.append(dict(item_code=c, item_name=n, item_group="Sub Assemblies", stock_uom=u, is_stock_item=1, is_purchase_item=0,
                      is_sales_item=0, include_item_in_manufacturing=1, valuation_rate=BOMCOST[c], weight_per_unit=wt, weight_uom="Kg",
                      description="In-house sub-assembly (make-to-stock, issued to work orders)",
                      default_material_request_type="Manufacture", item_defaults=item_defaults(WH_WIP)))
for c, (n, g, u, mode, wt, comps, ops, mg, cc, ro) in FG.items():
    d = dict(item_code=c, item_name=n, item_group=g, stock_uom=u, is_stock_item=1, is_purchase_item=0, is_sales_item=1,
             include_item_in_manufacturing=1, valuation_rate=BOMCOST[c], standard_rate=SELL[c], weight_per_unit=wt, weight_uom="Kg",
             description=f"{'Make-to-Stock' if mode == 'MTS' else 'Make-to-Order (project specific)'} - fabricated by KREATAO, Sharjah",
             default_material_request_type="Manufacture", item_defaults=item_defaults(WH_FG))
    if ro:
        d["reorder_levels"] = [dict(warehouse=WH_FG, warehouse_reorder_level=ro[0], warehouse_reorder_qty=ro[1], material_request_type="Manufacture")]
    items.append(d)
# fix item_defaults cost centre for FG
write("13_Item.csv", "Item", items,
      note="Raw materials, consumables, services, sub-assemblies and finished goods (MTS + MTO). "
           "Reorder levels on MTS items and yard stock drive auto Material Requests.")

# 14 Item prices
ip = []
for c, v in RM.items():
    ip.append(dict(item_code=c, price_list="Standard Buying", price_list_rate=v[3], currency="AED", valid_from="2026-01-01"))
ip.append(dict(item_code="SRV-GALV", price_list="Standard Buying", price_list_rate=1.45, currency="AED", valid_from="2026-01-01"))
ip.append(dict(item_code="SRV-TRANSPORT", price_list="Standard Buying", price_list_rate=650, currency="AED", valid_from="2026-01-01"))
for c in FG: ip.append(dict(item_code=c, price_list="Standard Selling", price_list_rate=SELL[c], currency="AED", valid_from="2026-01-01"))
for c, v in SERV.items():
    if v[3]: ip.append(dict(item_code=c, price_list="Standard Selling", price_list_rate=v[3], currency="AED", valid_from="2026-01-01"))
write("14_Item_Price.csv", "Item Price", ip)

# =========================================================================== PARTIES
SUP = [
    ("Falcon Steel Trading LLC", "Steel Mills & Traders", "Sharjah", "Hamriyah Free Zone Rd, Sharjah", "Omar Al Suwaidi", "Sales Manager", "100200300400011"),
    ("Emirates Coil & Sheet Industries FZE", "Steel Mills & Traders", "Jebel Ali, Dubai", "Plot 214, Jebel Ali Industrial Area 1, Dubai", "Priya Menon", "Key Accounts", "100200300400029"),
    ("Desert Rose Fasteners LLC", "Fasteners & Hardware Suppliers", "Dubai", "Al Quoz Industrial Area 3, Dubai", "Imran Qureshi", "Director", "100200300400037"),
    ("Pearl Weld Supplies LLC", "Welding & Gases", "Ajman", "Ajman Industrial Area 2, Ajman", "Sunil Varghese", "Sales Executive", "100200300400045"),
    ("Oasis Protective Coatings LLC", "Paints & Coatings Suppliers", "Sharjah", "Sharjah Industrial Area 17, Sharjah", "Layla Haddad", "Technical Sales", "100200300400052"),
    ("Al Mirage Galvanizing & Metal Treatment LLC", "Subcontract & Logistics", "Ajman", "Al Jurf Industrial Zone 3, Ajman", "Rashid Al Nuaimi", "Operations Manager", "100200300400060"),
    ("Horizon Heavy Haulage LLC", "Subcontract & Logistics", "Sharjah", "Sajaa Industrial Area, Sharjah", "Vikram Nair", "Fleet Manager", "100200300400078"),
    ("Sandstorm Industrial Gases LLC", "Welding & Gases", "Sharjah", "Sharjah Industrial Area 6, Sharjah", "Hassan Karim", "Account Manager", "100200300400086"),
]
CUS = [
    ("Burj Al Noor Contracting LLC", "Contractors & EPC", "Dubai", "Business Bay, Dubai", "Khalid Mansoor", "Procurement Manager", "100300400500014"),
    ("Sahara Industrial Parks Development LLC", "Developers", "Sharjah", "Sharjah Airport Intl Free Zone, Sharjah", "Noura Al Zaabi", "Project Director", "100300400500022"),
    ("Emirate Municipal Projects Office (Demo)", "Government & Municipal", "Abu Dhabi", "Khalifa Park District, Abu Dhabi", "Faisal Al Dhaheri", "Contracts Engineer", "100300400500030"),
    ("Al Reef Logistics & Warehousing LLC", "Industrial & Manufacturing", "Abu Dhabi", "ICAD 1, Mussafah, Abu Dhabi", "Sameer Joshi", "Facilities Head", "100300400500048"),
    ("Gulf Horizon Petrochemical Services LLC", "Industrial & Manufacturing", "Abu Dhabi", "Ruwais Industrial Complex, Al Dhafra", "Daniel Foster", "Package Engineer", "100300400500055"),
    ("Crescent Agro Processing FZC", "Industrial & Manufacturing", "Ras Al Khaimah", "RAKEZ Al Ghail, Ras Al Khaimah", "Mariam Al Shamsi", "Plant Manager", "100300400500063"),
    ("Northern Emirates Steel Erectors LLC", "Contractors & EPC", "Ajman", "Al Jurf Industrial 2, Ajman", "Abdul Rahman Siddiqui", "Purchase Lead", "100300400500071"),
    ("Dune Cold Storage LLC", "Industrial & Manufacturing", "Fujairah", "Fujairah Free Zone, Fujairah", "Ravi Shankar", "Operations Director", "100300400500089"),
    ("Marina Gate Infrastructure Projects LLC", "Contractors & EPC", "Dubai", "Dubai Investment Park 1, Dubai", "Elena Petrova", "Procurement Specialist", "100300400500097"),
    ("Al Batinah Steel Works SAOC", "Contractors & EPC", "Export - GCC", "Sohar Industrial Estate, Sohar, Oman", "Salim Al Harthy", "Purchasing Manager", ""),
]
write("15_Supplier.csv", "Supplier", [
    dict(supplier_name=n, supplier_group=g, supplier_type="Company", country="United Arab Emirates", default_currency="AED", tax_id=t)
    for n, g, _c, _a, _p, _d, t in SUP], note="TRNs are fictional.")
write("16_Customer.csv", "Customer", [
    dict(customer_name=n, customer_group=g, customer_type="Company", territory=ter if ter in EMIRATES else ter,
         default_currency="AED", default_price_list="Standard Selling", tax_id=t)
    for n, g, ter, _a, _p, _d, t in CUS], note="TRNs are fictional. Last customer is an Omani export customer (zero-rated).")

addr, cont = [], []
def split_addr(s): return [x.strip() for x in s.rsplit(",", 1)] if "," in s else [s, ""]
EMIRATE_OF = {"Dubai": "Dubai", "Jebel Ali, Dubai": "Dubai", "Sharjah": "Sharjah", "Ajman": "Ajman", "Abu Dhabi": "Abu Dhabi",
              "Ras Al Khaimah": "Ras Al Khaimah", "Fujairah": "Fujairah"}
def slug(n): return n.split()[0].lower()
for i, (n, g, ter, ad, pn, des, tax) in enumerate(SUP):
    l1, city = split_addr(ad)
    addr.append(dict(address_title=n, address_type="Billing", address_line1=l1, city=city or ter,
                     state=EMIRATE_OF.get(ter, ter), country="United Arab Emirates", phone=f"+971 6 555 01{10+i:02d}",
                     email_id=f"accounts@{slug(n)}.example", is_primary_address=1,
                     links=[dict(link_doctype="Supplier", link_name=n)]))
    f, l = pn.split(" ", 1)
    cont.append(dict(first_name=f, last_name=l, designation=des, status="Passive", company_name=n,
                     email_ids=[dict(email_id=f"{f.lower()}.{l.split()[-1].lower()}@{slug(n)}.example", is_primary=1)],
                     phone_nos=[dict(phone=f"+971 50 555 02{10+i:02d}", is_primary_mobile_no=1)],
                     links=[dict(link_doctype="Supplier", link_name=n)]))
for i, (n, g, ter, ad, pn, des, tax) in enumerate(CUS):
    l1, city = split_addr(ad)
    ctry = "Oman" if ter == "Export - GCC" else "United Arab Emirates"
    addr.append(dict(address_title=n, address_type="Billing", address_line1=l1, city=city or ter,
                     state=EMIRATE_OF.get(ter, ""), country=ctry, phone=f"+971 4 555 03{10+i:02d}" if ctry != "Oman" else "+968 2555 0311",
                     email_id=f"projects@{slug(n)}.example", is_primary_address=1, is_shipping_address=1,
                     links=[dict(link_doctype="Customer", link_name=n)]))
    f, l = pn.split(" ", 1)
    cont.append(dict(first_name=f, last_name=l, designation=des, status="Passive", company_name=n,
                     email_ids=[dict(email_id=f"{f.lower()}.{l.split()[-1].lower()}@{slug(n)}.example", is_primary=1)],
                     phone_nos=[dict(phone=f"+971 55 555 04{10+i:02d}", is_primary_mobile_no=1)],
                     links=[dict(link_doctype="Customer", link_name=n)]))
write("17_Address.csv", "Address", addr, note="Phones are +971 5xx-series demo numbers; e-mail domains use the reserved .example TLD.")
write("18_Contact.csv", "Contact", cont)

# =========================================================================== BOMs
def bom_doc(code):
    spec = SA.get(code) or FG.get(code)
    if code in SA: nm, uom, comps, ops = spec[0], spec[1], spec[2], spec[3]
    else: nm, uom, comps, ops = spec[0], spec[2], spec[5], spec[6]
    rows = []
    for c, q in comps:
        is_sa = c in SA
        uom_c = (RM[c][2] if c in RM else SA[c][1])
        r = dict(item_code=c, qty=q, uom=uom_c, stock_uom=uom_c, conversion_factor=1, rate=rate[c],
                 include_item_in_manufacturing=1)
        if is_sa: r["bom_no"] = f"BOM-{c}-001"
        rows.append(r)
    opr = [dict(operation=o, workstation=OPS[o][0], time_in_mins=m, hour_rate=WS[OPS[o][0]][1], sequence_id=i + 1)
           for i, (o, m) in enumerate(ops)]
    return dict(item=code, quantity=1, uom=uom, is_active=1, is_default=1, with_operations=1, company=CO, currency="AED",
                conversion_rate=1, rm_cost_as_per="Valuation Rate", transfer_material_against="Work Order",
                set_rate_of_sub_assembly_item_based_on_bom=1, items=rows, operations=opr)
write("19_BOM_SubAssemblies.csv", "BOM", [bom_doc(c) for c in SA], submit=True,
      note="Import first; tick 'Submit After Import'. Names are generated as BOM-<ITEM>-001.")
write("20_BOM_FinishedGoods.csv", "BOM", [bom_doc(c) for c in FG], submit=True,
      note="Import after the sub-assembly BOM file - sub-assembly rows reference BOM-<SA>-001. Tick 'Submit After Import'.")

# =========================================================================== INVENTORY / TRANSACTIONS
EV = []   # stock events for the simulator: (date, time, label, [(item, wh, +/-qty)])
def ev(date, time, label, lines): EV.append((date, time, label, lines))
def tax_rows(kind="sales", zero=False):
    r = dict(charge_type="On Net Total", account_head=VAT0 if zero else VAT, description="VAT 0% (Export)" if zero else "VAT 5%",
             rate=0 if zero else 5, cost_center=CC)
    if kind == "purchase": r.update(category="Total", add_deduct_tax="Add")
    return [r]

# 21 Opening stock
OPEN = {
    "RM-HB-300": 14000, "RM-IPE-200": 9000, "RM-UB-406": 11000, "RM-UC-203": 7000, "RM-PFC-150": 6000, "RM-ANG-75": 5000,
    "RM-RHS-100": 5000, "RM-PL-06": 4500, "RM-PL-10": 7000, "RM-PL-16": 5000, "RM-PL-20": 6000, "RM-FB-50": 1500,
    "RM-ZP-200": 4000, "RM-PPGL-05": 9000,
    "RM-BOLT-M20": 1500, "RM-BOLT-M16": 800, "RM-ANCH-M24": 400, "RM-SCR-TEK": 20000, "RM-WIRE-ER70": 600, "RM-ELEC-7018": 150,
    "RM-GAS-MIX": 40, "RM-PRIMER-ZP": 900, "RM-EPOXY-INT": 500, "RM-PU-FIN": 300, "RM-THINNER": 200, "RM-GRIT-G25": 4000, "CN-DISC-125": 300,
    "SA-BASEPLATE": 12, "SA-ENDPLATE": 20, "SA-STRINGER": 10,
    "FG-PURLIN-Z200": 200, "FG-ROOF-TR-05": 1500, "FG-STAIR-STD": 6,
}
def wh_of(c):
    if c in RM: return RM[c][5]
    if c in SA: return WH_WIP
    return WH_FG
OPEN_DATE = "2026-10-01"
sr_rows = [dict(item_code=c, warehouse=wh_of(c), qty=q, valuation_rate=(RM[c][3] if c in RM else BOMCOST[c])) for c, q in OPEN.items()]
write("21_Stock_Reconciliation_Opening.csv", "Stock Reconciliation", [dict(
    purpose="Opening Stock", naming_series="MAT-RECO-.YYYY.-", company=CO, posting_date=OPEN_DATE, posting_time="08:00:00", set_posting_time=1,
    expense_account=a("Temporary Opening"), cost_center=CC, items=sr_rows)], submit=True,
    note="Opening balances dated 2026-10-01 against Temporary Opening - KSSB.")
ev(OPEN_DATE, "08:00:00", "Opening stock", [(c, wh_of(c), q) for c, q in OPEN.items()])

# 22 Material requests (purchase)
MR = [
    dict(material_request_type="Purchase", company=CO, transaction_date="2026-11-03", schedule_date="2026-11-24", naming_series="MAT-MR-.YYYY.-",
         items=[dict(item_code="RM-HB-300", qty=20000, uom="Kg", schedule_date="2026-11-24", warehouse=WH_YARD),
                dict(item_code="RM-IPE-200", qty=8000, uom="Kg", schedule_date="2026-11-24", warehouse=WH_YARD),
                dict(item_code="RM-UC-203", qty=6000, uom="Kg", schedule_date="2026-11-24", warehouse=WH_YARD),
                dict(item_code="RM-PL-10", qty=5000, uom="Kg", schedule_date="2026-11-24", warehouse=WH_YARD)]),
    dict(material_request_type="Purchase", company=CO, transaction_date="2026-11-05", schedule_date="2026-11-20", naming_series="MAT-MR-.YYYY.-",
         items=[dict(item_code="RM-BOLT-M20", qty=1200, uom="Nos", schedule_date="2026-11-20", warehouse=WH_STORES),
                dict(item_code="RM-ANCH-M24", qty=300, uom="Nos", schedule_date="2026-11-20", warehouse=WH_STORES),
                dict(item_code="RM-PRIMER-ZP", qty=500, uom="Litre", schedule_date="2026-11-20", warehouse=WH_STORES),
                dict(item_code="RM-EPOXY-INT", qty=300, uom="Litre", schedule_date="2026-11-20", warehouse=WH_STORES)]),
]
write("22_Material_Request.csv", "Material Request", MR, submit=True, note="Open purchase requisitions (statuses stay 'Pending' until you create POs from them).")

# 23 Purchase orders (open, to be received)
def po(sup, date, sched, items_, note_=""):
    its = [dict(item_code=c, qty=q, rate=r, uom=u, schedule_date=sched, **({"warehouse": w} if not c.startswith("SRV-") else {})) for c, q, r, u, w in items_]
    return dict(supplier=sup, transaction_date=date, schedule_date=sched, company=CO, currency="AED", conversion_rate=1, buying_price_list="Standard Buying", price_list_currency="AED", plc_conversion_rate=1,
                naming_series="PUR-ORD-.YYYY.-", taxes_and_charges=T_VAT, items=its, taxes=tax_rows("purchase"))
POS = [
    po("Falcon Steel Trading LLC", "2026-11-05", "2026-11-24", [("RM-HB-300", 20000, 3.35, "Kg", WH_YARD), ("RM-IPE-200", 8000, 3.30, "Kg", WH_YARD),
                                                                   ("RM-UC-203", 6000, 3.40, "Kg", WH_YARD), ("RM-PL-10", 5000, 3.15, "Kg", WH_YARD)]),
    po("Desert Rose Fasteners LLC", "2026-11-06", "2026-11-20", [("RM-BOLT-M20", 1200, 3.80, "Nos", WH_STORES), ("RM-ANCH-M24", 300, 14.50, "Nos", WH_STORES)]),
    po("Oasis Protective Coatings LLC", "2026-11-06", "2026-11-20", [("RM-PRIMER-ZP", 500, 22.00, "Litre", WH_STORES), ("RM-EPOXY-INT", 300, 31.00, "Litre", WH_STORES)]),
    po("Emirates Coil & Sheet Industries FZE", "2026-11-09", "2026-11-27", [("RM-ZP-200", 2000, 20.90, "Meter", WH_YARD)]),
    po("Al Mirage Galvanizing & Metal Treatment LLC", "2026-11-10", "2026-12-05", [("SRV-GALV", 1500, 1.45, "Kg", WH_STORES)]),
]
write("23_Purchase_Order.csv", "Purchase Order", POS, submit=True, note="Open POs awaiting receipt (typical 'To Receive and Bill').")

# 24 Purchase receipts (historical, direct - no PO link so PO statuses stay clean)
def pr(sup, date, tm, items_):
    its = [dict(item_code=c, qty=q, rate=r, uom=u, stock_uom=u, conversion_factor=1, warehouse=w) for c, q, r, u, w in items_]
    return dict(supplier=sup, posting_date=date, posting_time=tm, set_posting_time=1, company=CO, currency="AED", conversion_rate=1,
                buying_price_list="Standard Buying", price_list_currency="AED", plc_conversion_rate=1, naming_series="MAT-PRE-.YYYY.-", items=its)
PRS = [
    pr("Falcon Steel Trading LLC", "2026-10-14", "10:00:00", [("RM-UB-406", 4000, 3.40, "Kg", WH_YARD), ("RM-PL-16", 3000, 3.20, "Kg", WH_YARD), ("RM-PL-20", 2000, 3.20, "Kg", WH_YARD)]),
    pr("Emirates Coil & Sheet Industries FZE", "2026-10-14", "14:00:00", [("RM-PPGL-05", 12000, 4.90, "Kg", WH_YARD), ("RM-ZP-200", 3000, 20.90, "Meter", WH_YARD)]),
    pr("Pearl Weld Supplies LLC", "2026-10-28", "09:30:00", [("RM-WIRE-ER70", 300, 8.20, "Kg", WH_STORES), ("RM-ELEC-7018", 100, 9.50, "Kg", WH_STORES), ("RM-GAS-MIX", 20, 140.00, "Nos", WH_STORES)]),
    pr("Desert Rose Fasteners LLC", "2026-10-28", "11:15:00", [("RM-BOLT-M20", 800, 3.80, "Nos", WH_STORES), ("RM-BOLT-M16", 400, 1.60, "Nos", WH_STORES),
                                                                  ("RM-ANCH-M24", 200, 14.50, "Nos", WH_STORES), ("RM-SCR-TEK", 10000, 0.12, "Nos", WH_STORES)]),
    pr("Oasis Protective Coatings LLC", "2026-11-04", "15:00:00", [("RM-PRIMER-ZP", 400, 22.00, "Litre", WH_STORES), ("RM-EPOXY-INT", 200, 31.00, "Litre", WH_STORES),
                                                                    ("RM-PU-FIN", 100, 38.00, "Litre", WH_STORES), ("RM-THINNER", 80, 9.00, "Litre", WH_STORES)]),
]
write("24_Purchase_Receipt.csv", "Purchase Receipt", PRS, submit=True, note="Goods received into Steel Yard / Stores (direct receipts).")
for p in PRS: ev(p["posting_date"], p["posting_time"], "PR " + p["supplier"], [(r["item_code"], r["warehouse"], r["qty"]) for r in p["items"]])

# 25 Purchase invoices (stock purchase with update_stock + subcontract service)
def pi(sup, date, bill, upd, items_, due):
    its = []
    for c, q, r, u, w, ex in items_:
        row = dict(item_code=c, qty=q, rate=r, uom=u, stock_uom=u, conversion_factor=1)
        if w: row["warehouse"] = w
        if ex: row["expense_account"] = ex
        its.append(row)
    return dict(supplier=sup, posting_date=date, set_posting_time=1, posting_time="12:00:00", bill_no=bill, bill_date=date, due_date=due, company=CO,
                currency="AED", conversion_rate=1, buying_price_list="Standard Buying", price_list_currency="AED", plc_conversion_rate=1,
                credit_to=a("Creditors"), naming_series="ACC-PINV-.YYYY.-", update_stock=upd,
                taxes_and_charges=T_VAT, items=its, taxes=tax_rows("purchase"))
PIS = [
    pi("Sandstorm Industrial Gases LLC", "2026-10-31", "SIG-INV-26-2207", 1, [("RM-GAS-MIX", 12, 140.00, "Nos", WH_STORES, None), ("CN-DISC-125", 120, 6.50, "Nos", WH_STORES, None)], "2026-11-30"),
    pi("Al Mirage Galvanizing & Metal Treatment LLC", "2026-11-02", "AMG-26-00431", 0, [("SRV-GALV", 3200, 1.45, "Kg", None, a("Galvanizing Subcontract Charges"))], "2026-12-02"),
    pi("Horizon Heavy Haulage LLC", "2026-11-08", "HHH-26-1189", 0, [("SRV-TRANSPORT", 4, 650.00, "Nos", None, a("Freight and Forwarding Charges"))], "2026-12-08"),
]
write("25_Purchase_Invoice.csv", "Purchase Invoice", PIS, submit=True,
      note="One direct stock purchase (update_stock=1) and two service invoices. PR->PI billing links are left for you to demo from the UI.")
ev("2026-10-31", "12:00:00", "PI gases", [("RM-GAS-MIX", WH_STORES, 12), ("CN-DISC-125", WH_STORES, 120)])

# 26 Quotations
def qtn(cust, date, valid, items_, zero=False):
    its = [dict(item_code=c, qty=q, rate=r, uom=u) for c, q, r, u in items_]
    return dict(quotation_to="Customer", party_name=cust, transaction_date=date, valid_till=valid, order_type="Sales", company=CO, currency="AED", conversion_rate=1,
                selling_price_list="Standard Selling", price_list_currency="AED", plc_conversion_rate=1, naming_series="SAL-QTN-.YYYY.-", taxes_and_charges=T_VAT0 if zero else T_VAT,
                items=its, taxes=tax_rows("sales", zero))
QS = [
    qtn("Sahara Industrial Parks Development LLC", "2026-10-05", "2026-11-04", [("FG-PEB-FRAME-30", 6, SELL["FG-PEB-FRAME-30"], "Nos"), ("SRV-DETAIL", 24, 120.00, "Nos")]),
    qtn("Al Reef Logistics & Warehousing LLC", "2026-10-08", "2026-11-07", [("FG-MEZZ-BEAM-12", 14, SELL["FG-MEZZ-BEAM-12"], "Nos"), ("SRV-ERECT", 18, 780.00, "Tonne")]),
    qtn("Marina Gate Infrastructure Projects LLC", "2026-10-20", "2026-11-19", [("FG-PIPE-RACK-6M", 8, SELL["FG-PIPE-RACK-6M"], "Nos")]),
    qtn("Emirate Municipal Projects Office (Demo)", "2026-11-02", "2026-12-02", [("FG-ROOF-TRUSS-24", 10, SELL["FG-ROOF-TRUSS-24"], "Nos"), ("FG-ROOF-TR-05", 3000, SELL["FG-ROOF-TR-05"], "Square Meter")]),
    qtn("Al Batinah Steel Works SAOC", "2026-11-06", "2026-12-06", [("FG-PURLIN-Z200", 600, SELL["FG-PURLIN-Z200"], "Nos"), ("FG-ROOF-TR-05", 1500, SELL["FG-ROOF-TR-05"], "Square Meter")], zero=True),
]
write("26_Quotation.csv", "Quotation", QS, submit=True, note="Open quotations (one zero-rated export quotation).")

# 27 Sales orders (MTO projects + open MTS orders). Order of rows == SAL-ORD-2026-0000N sequence.
def so(cust, date, deliv, po_no, items_, zero=False):
    its = [dict(item_code=c, qty=q, rate=r, uom=u, delivery_date=deliv, **({"warehouse": WH_FG} if c.startswith("FG-") else {})) for c, q, r, u in items_]
    return dict(customer=cust, transaction_date=date, delivery_date=deliv, order_type="Sales", company=CO, currency="AED", conversion_rate=1,
                selling_price_list="Standard Selling", price_list_currency="AED", plc_conversion_rate=1, naming_series="SAL-ORD-.YYYY.-", po_no=po_no, po_date=date,
                taxes_and_charges=T_VAT0 if zero else T_VAT, items=its, taxes=tax_rows("sales", zero))
SOS = [
    so("Sahara Industrial Parks Development LLC", "2026-10-12", "2026-12-20", "SIP/PO/2026/0412",
       [("FG-PEB-FRAME-30", 6, SELL["FG-PEB-FRAME-30"], "Nos"), ("SRV-DETAIL", 24, 120.00, "Nos")]),
    so("Al Reef Logistics & Warehousing LLC", "2026-10-15", "2027-01-05", "ARL-MEZZ-8841",
       [("FG-MEZZ-BEAM-12", 14, SELL["FG-MEZZ-BEAM-12"], "Nos"), ("SRV-ERECT", 18, 780.00, "Tonne")]),
    so("Crescent Agro Processing FZC", "2026-10-19", "2026-12-15", "CAP-26-0097",
       [("FG-ROOF-TRUSS-24", 4, SELL["FG-ROOF-TRUSS-24"], "Nos"), ("FG-ROOF-TR-05", 900, SELL["FG-ROOF-TR-05"], "Square Meter")]),
    so("Gulf Horizon Petrochemical Services LLC", "2026-10-21", "2027-01-20", "GHP-RUW-55120",
       [("FG-CRANE-GIRDER-10T", 2, SELL["FG-CRANE-GIRDER-10T"], "Nos"), ("SRV-TRANSPORT", 2, 850.00, "Nos")]),
    so("Burj Al Noor Contracting LLC", "2026-10-26", "2027-01-12", "BAN/KSSB/0233",
       [("FG-PIPE-RACK-6M", 5, SELL["FG-PIPE-RACK-6M"], "Nos"), ("FG-PLAT-ACCESS", 3, SELL["FG-PLAT-ACCESS"], "Nos")]),
    so("Northern Emirates Steel Erectors LLC", "2026-11-02", "2026-11-18", "NESE-PO-7714",
       [("FG-PURLIN-Z200", 200, SELL["FG-PURLIN-Z200"], "Nos"), ("FG-STAIR-STD", 4, SELL["FG-STAIR-STD"], "Nos")]),
]
write("27_Sales_Order.csv", "Sales Order", SOS, submit=True,
      note="Rows 1-5 are Make-to-Order projects (linked to work orders); row 6 is a Make-to-Stock order served from finished-goods stock. "
           "The Work Order file references SAL-ORD-2026-00001..00005 - see README if your site already has Sales Orders.")

# 28 Work orders
def wo(item, qty, so_name, start, end, mode):
    d = dict(naming_series="MFG-WO-.YYYY.-", production_item=item, bom_no=f"BOM-{item}-001", qty=qty, company=CO,
             use_multi_level_bom=1 if mode == "MTO" else 0, fg_warehouse=WH_FG, wip_warehouse=WH_WIP,
             planned_start_date=start + " 07:30:00", planned_end_date=end + " 17:30:00", status="Draft")
    if so_name: d["sales_order"] = so_name
    return d
SO_NAME = lambda i: f"SAL-ORD-2026-{i:05d}"
WOS = [
    wo("FG-PEB-FRAME-30", 6, SO_NAME(1), "2026-11-16", "2026-12-08", "MTO"),
    wo("FG-MEZZ-BEAM-12", 14, SO_NAME(2), "2026-11-23", "2026-12-18", "MTO"),
    wo("FG-ROOF-TRUSS-24", 4, SO_NAME(3), "2026-11-18", "2026-12-04", "MTO"),
    wo("FG-CRANE-GIRDER-10T", 2, SO_NAME(4), "2026-12-07", "2026-12-30", "MTO"),
    wo("FG-PIPE-RACK-6M", 5, SO_NAME(5), "2026-12-01", "2026-12-28", "MTO"),
    wo("FG-PLAT-ACCESS", 3, SO_NAME(5), "2026-12-14", "2026-12-24", "MTO"),
    wo("FG-STAIR-STD", 10, "", "2026-11-17", "2026-11-26", "MTS"),
    wo("FG-PURLIN-Z200", 400, "", "2026-11-19", "2026-11-23", "MTS"),
]
write("28_Work_Order.csv", "Work Order", WOS, submit=True,
      note="Planned production: 6 MTO work orders (linked to Sales Orders) + 2 MTS replenishment orders. "
           "Submitting auto-creates required items and Job Cards from the BOM operations.")

# 29 Manufacture stock entries (completed historical MTS production, independent of work orders)
def mfg(item, qty, date, tm):
    spec = SA.get(item) or FG.get(item)
    comps, ops = (spec[2], spec[3]) if item in SA else (spec[5], spec[6])
    rows = []
    lines = []
    for c, q in comps:
        qq = round(q * qty, 3)
        u = RM[c][2] if c in RM else SA[c][1]
        w = wh_of(c)
        rows.append(dict(item_code=c, qty=qq, s_warehouse=w, uom=u, stock_uom=u, conversion_factor=1, transfer_qty=qq))
        lines.append((c, w, -qq))
    fu = SA[item][1] if item in SA else spec[2]
    tw = WH_WIP if item in SA else WH_FG
    rows.append(dict(item_code=item, qty=qty, t_warehouse=tw, uom=fu, stock_uom=fu, conversion_factor=1, transfer_qty=qty, is_finished_item=1))
    lines.append((item, tw, qty))
    ev(date, tm, f"MFG {item} x{qty}", lines)
    conv = round(op_cost(ops) * qty, 2)
    return dict(naming_series="MAT-STE-.YYYY.-", stock_entry_type="Manufacture", purpose="Manufacture", company=CO, posting_date=date, posting_time=tm, set_posting_time=1,
                from_bom=1, bom_no=f"BOM-{item}-001", fg_completed_qty=qty, use_multi_level_bom=0,
                from_warehouse=WH_YARD, to_warehouse=tw, items=rows,
                additional_costs=[dict(expense_account=a("Expenses Included In Valuation"), description="Workshop conversion cost (labour, machine, power)", amount=conv)])
SES = [
    mfg("FG-PURLIN-Z200", 300, "2026-10-08", "09:00:00"),
    mfg("FG-ROOF-TR-05", 2000, "2026-10-15", "16:00:00"),
    mfg("SA-BASEPLATE", 40, "2026-10-20", "10:00:00"),
    mfg("FG-STAIR-STD", 8, "2026-10-22", "11:00:00"),
    mfg("SA-ENDPLATE", 60, "2026-11-05", "10:30:00"),
    mfg("FG-PURLIN-Z200", 400, "2026-11-09", "09:00:00"),
]
write("29_Stock_Entry_Manufacture.csv", "Stock Entry", SES, submit=True,
      note="Completed make-to-stock production (finished goods + sub-assemblies) posted as independent Manufacture entries "
           "with workshop conversion cost capitalised via Expenses Included In Valuation.")

# 30 Delivery notes (ex-stock, awaiting billing)
def dn(cust, date, tm, items_):
    its = [dict(item_code=c, qty=q, rate=r, uom=u, stock_uom=u, conversion_factor=1, warehouse=WH_FG) for c, q, r, u in items_]
    ev(date, tm, "DN " + cust, [(c, WH_FG, -q) for c, q, r, u in items_])
    return dict(customer=cust, posting_date=date, posting_time=tm, set_posting_time=1, company=CO, currency="AED", conversion_rate=1, selling_price_list="Standard Selling", price_list_currency="AED", plc_conversion_rate=1,
                naming_series="MAT-DN-.YYYY.-", taxes_and_charges=T_VAT, items=its, taxes=tax_rows("sales"))
DNS = [
    dn("Al Reef Logistics & Warehousing LLC", "2026-11-12", "10:00:00", [("FG-PURLIN-Z200", 100, SELL["FG-PURLIN-Z200"], "Nos"), ("FG-ROOF-TR-05", 500, SELL["FG-ROOF-TR-05"], "Square Meter")]),
    dn("Dune Cold Storage LLC", "2026-11-12", "14:00:00", [("FG-STAIR-STD", 3, SELL["FG-STAIR-STD"], "Nos")]),
]
write("30_Delivery_Note.csv", "Delivery Note", DNS, submit=True, note="Delivered, billing pending ('To Bill').")

# 31 Sales invoices (ex-stock with update_stock=1, incl. zero-rated export)
def si(cust, date, tm, items_, zero=False, terms=30):
    its = [dict(item_code=c, qty=q, rate=r, uom=u, stock_uom=u, conversion_factor=1, warehouse=WH_FG, cost_center=cc)
           for c, q, r, u, cc in items_]
    ev(date, tm, "SI " + cust, [(c, WH_FG, -q) for c, q, r, u, cc in items_])
    return dict(customer=cust, posting_date=date, posting_time=tm, set_posting_time=1, due_date=plus(date, terms), company=CO, currency="AED", conversion_rate=1,
                selling_price_list="Standard Selling", price_list_currency="AED", plc_conversion_rate=1, debit_to=a("Debtors"), naming_series="ACC-SINV-.YYYY.-", update_stock=1,
                taxes_and_charges=T_VAT0 if zero else T_VAT, items=its, taxes=tax_rows("sales", zero))
SIS = [
    si("Burj Al Noor Contracting LLC", "2026-10-24", "11:00:00", [("FG-PURLIN-Z200", 150, SELL["FG-PURLIN-Z200"], "Nos", CC_ROOF)]),
    si("Crescent Agro Processing FZC", "2026-10-30", "15:00:00", [("FG-ROOF-TR-05", 1200, SELL["FG-ROOF-TR-05"], "Square Meter", CC_ROOF)]),
    si("Northern Emirates Steel Erectors LLC", "2026-11-06", "12:00:00", [("FG-STAIR-STD", 2, SELL["FG-STAIR-STD"], "Nos", CC_STRUCT)]),
    si("Al Batinah Steel Works SAOC", "2026-11-10", "10:00:00", [("FG-PURLIN-Z200", 300, SELL["FG-PURLIN-Z200"], "Nos", CC_ROOF),
                                                                  ("FG-ROOF-TR-05", 800, SELL["FG-ROOF-TR-05"], "Square Meter", CC_ROOF)], zero=True, terms=45),
]
write("31_Sales_Invoice.csv", "Sales Invoice", SIS, submit=True,
      note="Ex-stock catalogue sales (invoice + stock issue in one document). Last invoice is a zero-rated export to Oman.")

# =========================================================================== MANIFEST + STOCK SIMULATION
FILES.sort(key=lambda f: f["file"])
json.dump(dict(files=FILES, bom_cost=BOMCOST, sell=SELL), open(os.path.join(OUT, "..", "manifest.json"), "w"), indent=1)
json.dump(EV, open(os.path.join(OUT, "..", "events.json"), "w"))
print("files:", len(FILES), "-> ", OUT)
for k, v in BOMCOST.items(): print(f"  cost {k:22s} {v:>10.2f}   sell {SELL.get(k)}")
