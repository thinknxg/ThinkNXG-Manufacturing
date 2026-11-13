# KREATAO UAE - Structural Steel Fabrication & Building Systems
## ERPNext v16 import-ready manufacturing demo dataset (CSV package)

| | |
|---|---|
| Company | **KREATAO Structural Steel & Building Systems LLC** (abbr **KSSB**) |
| Country / currency | United Arab Emirates / **AED** |
| VAT | **5 %** (ERPNext's own `UAE VAT 5% - KSSB` templates; export customer uses `UAE VAT Zero - KSSB`) |
| Manufacturing modes | **Make-to-Order** (6 project products) and **Make-to-Stock** (3 catalogue products + 3 sub-assemblies) |
| Data | 100 % fictional - customers, suppliers, TRNs, phone numbers, e-mails (`.example`), PO numbers |
| Built against | `frappe/erpnext` and `frappe/frappe` branch **version-16** (doctype JSON + Data Import code read directly) |

## 1. How to import

1. Use a **fresh v16 site** (or a site with no Sales Orders - see section 4).
2. For each row of the table below, in order: **Data Import -> New** -> pick the DocType -> *Import Type* = **Insert New Records** -> attach the CSV -> *Date Format* `yyyy-mm-dd` -> **Start Import**. Tick **Submit After Import** only where the table says so.
3. Each file's column headers are v16 *fieldnames*; child tables are written `table.fieldname` (e.g. `items.item_code`) - the v16 importer matches these directly, so no column mapping is needed.
4. Wait for every import to finish with 0 failures before starting the next file.

`IMPORT_ORDER.csv` carries the same table with per-file notes.

| Step | File | DocType | Docs | Submit |
|---|---|---|---|---|
| 0 | `00_prereq_Fiscal_Year_2026.csv` | Fiscal Year | 1 | - |
| 1 | `01_Company.csv` | Company | 1 | - |
| 2 | `02_Account.csv` | Account | 4 | - |
| 3 | `03_Cost_Center.csv` | Cost Center | 4 | - |
| 4 | `04_Warehouse.csv` | Warehouse | 4 | - |
| 5 | `05_UOM.csv` | UOM | 2 | - |
| 6 | `06_Item_Group.csv` | Item Group | 11 | - |
| 7 | `07_Customer_Group.csv` | Customer Group | 4 | - |
| 8 | `08_Supplier_Group.csv` | Supplier Group | 5 | - |
| 9 | `09_Territory.csv` | Territory | 8 | - |
| 10 | `10_Workstation_Type.csv` | Workstation Type | 7 | - |
| 11 | `11_Workstation_Operating_Component.csv` | Workstation Operating Component | 3 | - |
| 12 | `12_Workstation.csv` | Workstation | 10 | - |
| 13 | `13_Operation.csv` | Operation | 9 | - |
| 14 | `14_Item.csv` | Item | 43 | - |
| 15 | `15_Item_Price.csv` | Item Price | 41 | - |
| 16 | `16_Supplier.csv` | Supplier | 8 | - |
| 17 | `17_Customer.csv` | Customer | 10 | - |
| 18 | `18_Address.csv` | Address | 18 | - |
| 19 | `19_Contact.csv` | Contact | 18 | - |
| 20 | `20_BOM_SubAssemblies.csv` | BOM | 3 | **Yes** |
| 21 | `21_BOM_FinishedGoods.csv` | BOM | 9 | **Yes** |
| 22 | `22_Stock_Reconciliation_Opening.csv` | Stock Reconciliation | 1 | **Yes** |
| 23 | `23_Material_Request.csv` | Material Request | 2 | **Yes** |
| 24 | `24_Purchase_Order.csv` | Purchase Order | 5 | **Yes** |
| 25 | `25_Purchase_Receipt.csv` | Purchase Receipt | 5 | **Yes** |
| 26 | `26_Purchase_Invoice.csv` | Purchase Invoice | 3 | **Yes** |
| 27 | `27_Quotation.csv` | Quotation | 5 | **Yes** |
| 28 | `28_Sales_Order.csv` | Sales Order | 6 | **Yes** |
| 29 | `29_Work_Order.csv` | Work Order | 8 | **Yes** |
| 30 | `30_Stock_Entry_Manufacture.csv` | Stock Entry | 6 | **Yes** |
| 31 | `31_Delivery_Note.csv` | Delivery Note | 2 | **Yes** |
| 32 | `32_Sales_Invoice.csv` | Sales Invoice | 4 | **Yes** |

Strategy as requested: **master data (steps 0-19) -> BOMs (20-21) -> inventory & procurement (22-26) -> sales & manufacturing transactions (27-32)**.

## 2. What is in the dataset

**Masters** - 4 cost centres (Structural / PEB / Roofing / Projects), 4 extra warehouses (Steel Yard, Dispatch Yard, Scrap & Offcuts, Quarantine & Rejected) on top of ERPNext's defaults, 9 operations, 10 workstations with working hours and cost components (electricity / machine / labour -> AED 70-180 per hour), 43 items, 41 item prices, 8 suppliers and 10 customers with addresses and contacts.

**Items** - 27 raw materials & consumables (sections, plates, coil, purlins, bolts, welding, paint, abrasives), 4 services (erection, galvanizing subcontract, detailing, transport), 3 sub-assemblies, 9 finished goods:

| Mode | Items |
|---|---|
| Make-to-Stock (reorder levels set) | Z-Purlin 200x2.0, Trapezoidal roofing sheet 0.5 mm, Standard industrial staircase |
| Make-to-Order (project) | PEB 30 m portal frame, Mezzanine beam UB406, 24 m roof truss, 10 T crane girder, pipe rack module, access platform |

**BOMs** - 12 multi-level, with-operations BOMs (3 sub-assembly + 9 finished goods). Costing is rolled up bottom-up (raw material valuation + workstation hour rate x minutes) and selling prices carry a 20-26 % margin over that cost.

**Opening position (2026-10-01)** - AED 565,472 of stock across Steel Yard, Stores, WIP and Finished Goods.

**Transactions (Oct - Nov 2026)**

| Flow | What you get |
|---|---|
| Procurement | 2 purchase Material Requests, 5 open POs (incl. a galvanizing service PO), 5 received Purchase Receipts, 3 Purchase Invoices (1 direct stock purchase, 2 service bills) |
| Sales | 5 Quotations (1 zero-rated export), 6 Sales Orders (AED 340k net: 5 MTO projects, 1 MTS), 2 Delivery Notes awaiting billing, 4 Sales Invoices (incl. export to Oman at 0 %) |
| MTO production | 6 submitted Work Orders linked to Sales Orders 1-5, multi-level BOM, job cards generated from BOM operations |
| MTS production | 2 planned replenishment Work Orders + 6 completed Manufacture stock entries (finished goods and sub-assemblies, conversion cost capitalised) |
| Shortage demo | PEB frames need 18,330 kg of HB300 vs 14,000 kg on hand -> open PO + Material Request cover it |

## 3. Suggested demo walk-through
* **MTO**: Quotation -> Sales Order (SAL-ORD-2026-00001, Sahara, 6 PEB frames) -> Work Order -> *Start* -> Job Cards per operation -> Manufacture entry -> Delivery Note -> Invoice.
* **MTS**: open *Stock Projected Qty* - purlins, roofing sheets and staircases show reorder levels; raise a Manufacture Material Request or Production Plan.
* **Capacity**: Workstation calendar / Job Card schedule (07:00-12:00, 13:00-17:30).
* **VAT**: Sales Invoice 4 (Al Batinah, Oman) is zero-rated; all others carry 5 %.

## 4. Things you must know (read before importing)

1. **Work Orders point at Sales Orders by name.** v16 Data Import ignores a supplied document name for series-named doctypes, so the Work Order file expects the six Sales Orders to be created as `SAL-ORD-2026-00001` ... `00005` (series starting at 1, imported in 2026). On a site that already has Sales Orders, or in another year, search/replace those five names in the Work Order CSV before importing it.
2. **Deliberately unlinked documents.** Child-row IDs cannot be supplied in CSV, so Purchase Receipts, Purchase Invoices, Delivery Notes, Sales Invoices and Sales Orders are not cross-linked (e.g. the PRs are direct receipts, so the open POs stay *To Receive and Bill*). This avoids double stock/GL posting; create the linked versions from the UI ("Create" menu) if you want to demo billing against receipts.
3. **Independent Manufacture entries.** Completed MTS production is posted as Manufacture stock entries without a Work Order, because a Work-Order-linked entry would require job-card and transfer sequencing that cannot be expressed safely in CSV. The two MTS Work Orders (STAIR x10, PURLIN x400) are the next planned batches.
4. **Chart of accounts**: the Company file uses ERPNext's *Standard* template (it contains Temporary Opening, Stock Adjustment, Expenses Included in Valuation, Duties and Taxes). The separate *U.A.E - Chart of Accounts* template lacks several of these, so files 02, 22 and 30 would need re-pointing if you switch.
5. **Auto-created by ERPNext on Company insert** (not in the CSVs): the chart of accounts, Stores / Work In Progress / Finished Goods / Goods In Transit warehouses, `Main - KSSB` cost centre, UAE VAT templates and the `VAT 5% - KSSB` / `VAT Zero - KSSB` accounts, and enabling of AED.
6. `00_prereq_Fiscal_Year_2026.csv` is optional - skip it if Fiscal Year 2026 already exists.
7. No Holiday List is shipped; add one if you want working-day-aware scheduling (many UAE workshops run Saturday-Thursday).
8. Everything is dated 2026-10-01 to 2026-12-30; no back-dating permission is needed, but stock postings assume the opening reconciliation is imported first.

## 5. Verification performed (and what was *not* possible)

Run on the generated files with `tools/validate.py` and `tools/stocksim.py`:

* all 33 files: every column exists in the v16 DocType (parent or child table), every Select value is a legal option, no mandatory field left empty, every Link target is either defined in the package or is a known ERPNext default;
* stock simulation of all 19 stock events in date order: **0 negative balances** in any item/warehouse;
* BOM costs, selling prices and quantities are generated from one source (`tools/gen.py`), so BOMs, manufacture entries and prices cannot drift apart.

**Not done:** the package has not been imported into a running ERPNext v16 bench (none was available in this environment). Treat the first import as a dry run on a throw-away site; the most likely items to need adjustment are submit-time validations (Work Order, Manufacture entries) if your site's Manufacturing / Stock Settings differ from defaults.

## 6. Regenerating
`python3 tools/gen.py ./csv` rewrites all CSVs plus `manifest.json` / `events.json` one level up (edit the data tables in the script to change items, rates, parties or dates). `tools/validate.py ./csv` needs `ERPNEXT_APP` and `FRAPPE_APP` pointing at v16 checkouts (e.g. `.../erpnext/erpnext`, `.../frappe/frappe`); `tools/stocksim.py events.json` re-runs the stock check.
