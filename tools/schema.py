"""Doctype schema loader (reads frappe/erpnext v16 JSON) used by generator + validator."""
import json, os, glob, re
ROOTS = [os.environ.get("ERPNEXT_APP", "/home/claude/src/erpnext/erpnext"), os.environ.get("FRAPPE_APP", "/home/claude/src/frappe/frappe")]  # set ERPNEXT_APP / FRAPPE_APP to your v16 checkouts
_cache = {}
def scrub(n): return re.sub(r"[ \-]", "_", n).lower()
def load(doctype):
    if doctype in _cache: return _cache[doctype]
    s = scrub(doctype)
    hits = []
    for r in ROOTS:
        hits += glob.glob(f"{r}/**/doctype/{s}/{s}.json", recursive=True)
    if not hits: raise KeyError(doctype)
    d = json.load(open(hits[0]))
    _cache[doctype] = d
    return d
LAYOUT = {"Section Break","Column Break","Tab Break","HTML","Button","Heading","Fold","Image"}
def fields(doctype):
    return {f["fieldname"]: f for f in load(doctype)["fields"] if f["fieldtype"] not in LAYOUT}
