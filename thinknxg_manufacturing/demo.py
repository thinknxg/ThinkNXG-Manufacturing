"""Ordered loader for the KSSB UAE manufacturing demo dataset (ERPNext v16).

Runs every CSV listed in data/IMPORT_ORDER.csv through Frappe's own Data Import
(the same code path as Data Import -> New -> Start Import in the UI).

* Triggered automatically after install / migrate (after_install, after_migrate)
  as a background job, so it works on Frappe Cloud without SSH.
* Safe to re-run: steps that already succeeded are skipped.
* Stops at the first step that fails, so later steps never run on bad data.

Manual use (bench):
    bench --site <site> execute thinknxg_manufacturing.demo.load
    bench --site <site> execute thinknxg_manufacturing.demo.load --kwargs "{'retry_step': 28}"

Status without a console (log in as System Manager, open in the browser):
    /api/method/thinknxg_manufacturing.demo.status
"""

import csv
import os
import re

import frappe

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_DIR = os.path.join(DATA_DIR, "csv")
JOB_ID = "thinknxg_manufacturing_demo_load"
COMPANY = "KREATAO Structural Steel & Building Systems LLC"
MASTER_LAST_STEP = 19  # steps 0-19 tolerate "already exists" duplicates
WORK_ORDER_STEP = 29


# --------------------------------------------------------------------------- steps


def read_steps():
    steps = []
    with open(os.path.join(DATA_DIR, "IMPORT_ORDER.csv"), newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            steps.append(
                frappe._dict(
                    step=int(r["Step"]),
                    file=r["File"],
                    doctype=r["DocType"],
                    docs=int(r["Documents"]),
                    submit=r["Submit After Import"].strip().lower() in ("yes", "1", "true"),
                )
            )
    return steps


def _prior_import(step):
    """Latest Data Import created by this loader for this CSV file, if any."""
    stem = os.path.splitext(step.file)[0]
    for name in frappe.get_all(
        "File",
        filters={"attached_to_doctype": "Data Import", "file_name": ["like", stem + "%"]},
        pluck="attached_to_name",
        order_by="creation desc",
    ):
        if name and frappe.db.exists("Data Import", name):
            return frappe.get_doc("Data Import", name)
    return None


def _success_count(data_import):
    return frappe.db.count("Data Import Log", {"data_import": data_import, "success": 1})


def _failures(data_import, limit=10):
    return frappe.get_all(
        "Data Import Log",
        filters={"data_import": data_import, "success": 0},
        fields=["row_indexes", "messages", "exception"],
        limit=limit,
        order_by="log_index",
    )


def _already_present(step):
    """Prerequisites that may legitimately exist on the site already."""
    if step.step == 0:
        return bool(
            frappe.db.sql(
                "select name from `tabFiscal Year` where year_start_date <= '2026-10-01' and year_end_date >= '2026-10-01' limit 1"
            )
        )
    if step.step == 1:
        return bool(frappe.db.exists("Company", COMPANY))
    return False


def _is_duplicate(row):
    text = (row.get("exception") or "") + (row.get("messages") or "")
    return "already exists" in text or "Duplicate" in text or "DuplicateEntry" in text


def remap_sales_orders(text, names):
    """Point Work Order rows at the Sales Orders that really exist on this site.

    The CSV expects SAL-ORD-2026-00001..5. On a site whose Sales Order series
    is not at zero the imported names differ, so map Nth -> Nth created.
    """

    def repl(m):
        idx = int(m.group(1)) - 1
        return names[idx] if 0 <= idx < len(names) else m.group(0)

    return re.sub(r"SAL-ORD-2026-(\d{5})", repl, text)


# --------------------------------------------------------------------------- import


def _run_import(step, content):
    di = frappe.new_doc("Data Import")
    di.reference_doctype = step.doctype
    di.import_type = "Insert New Records"
    di.submit_after_import = 1 if step.submit else 0
    di.mute_emails = 1
    di.insert(ignore_permissions=True)

    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": step.file,
            "attached_to_doctype": "Data Import",
            "attached_to_name": di.name,
            "attached_to_field": "import_file",
            "is_private": 1,
            "content": content,
        }
    ).insert(ignore_permissions=True)
    di.db_set("import_file", file_doc.file_url)
    frappe.db.commit()

    from frappe.core.doctype.data_import.data_import import start_import

    start_import(di.name)  # synchronous; errors are recorded on the Data Import
    frappe.db.commit()
    return di.name


def _evaluate(step, data_import_name):
    status, warnings = frappe.db.get_value("Data Import", data_import_name, ["status", "template_warnings"])
    ok = _success_count(data_import_name)
    failed = _failures(data_import_name)
    if status == "Success" or ok >= step.docs:
        return True, f"{ok}/{step.docs} imported", status
    if (
        step.step <= MASTER_LAST_STEP
        and failed
        and ok + len(failed) >= step.docs
        and all(_is_duplicate(f) for f in failed)
    ):
        return True, f"{ok}/{step.docs} imported, rest already existed", status
    detail = []
    if warnings:
        detail.append(f"template warnings: {warnings[:500]}")
    for f in failed[:3]:
        exc = (f.get("exception") or "").strip().splitlines()
        detail.append(f"rows {f.get('row_indexes')}: {exc[-1] if exc else f.get('messages')}")
    return False, f"{ok}/{step.docs} imported; " + " | ".join(detail), status


class _Echo(list):
    def append(self, x):
        print(x, flush=True)
        super().append(x)


def load(start_step=0, retry_step=None):
    """Run all steps in order. Returns a list of per-step result strings."""
    frappe.set_user("Administrator")
    results = _Echo()
    for step in read_steps():
        if step.step < int(start_step):
            continue

        if _already_present(step):
            results.append(f"step {step.step:>2} {step.file}: skipped (already on site)")
            continue

        prior = _prior_import(step)
        if prior and step.step != retry_step:
            if prior.status == "Success":
                results.append(f"step {step.step:>2} {step.file}: done earlier ({prior.name})")
                continue
            if _success_count(prior.name) > 0:
                msg = (
                    f"step {step.step} {step.file}: earlier import {prior.name} is '{prior.status}' with "
                    f"{_success_count(prior.name)}/{step.docs} rows. Fix it from Data Import ({prior.name}) "
                    f"or delete the partial records, then run load(retry_step={step.step})."
                )
                results.append(msg)
                _log(results, failed=True)
                return results

        path = os.path.join(CSV_DIR, step.file)
        with open(path, "rb") as f:
            content = f.read()

        if step.step == WORK_ORDER_STEP:
            names = frappe.get_all(
                "Sales Order",
                filters={"company": COMPANY, "docstatus": 1},
                pluck="name",
                order_by="creation asc, name asc",
            )
            if len(names) < 5:
                results.append(f"step {step.step}: only {len(names)} submitted Sales Orders for KSSB, need 5. Stopped.")
                _log(results, failed=True)
                return results
            content = remap_sales_orders(content.decode("utf-8"), names).encode("utf-8")

        try:
            name = _run_import(step, content)
            ok, detail, status = _evaluate(step, name)
        except Exception:
            frappe.db.rollback()
            frappe.log_error(title=f"KSSB demo load: step {step.step} {step.file}")
            results.append(f"step {step.step:>2} {step.file}: EXCEPTION (see Error Log). Stopped.")
            _log(results, failed=True)
            return results

        results.append(f"step {step.step:>2} {step.file}: {'OK' if ok else 'FAILED'} - {detail} [{name}, {status}]")
        if not ok:
            _log(results, failed=True)
            return results

    _log(results, failed=False)
    return results


def _log(results, failed):
    frappe.log_error(
        title="KSSB demo load " + ("STOPPED" if failed else "finished"),
        message="\n".join(results),
    )
    frappe.db.commit()


# --------------------------------------------------------------------------- hooks / API


def _pending():
    pending = []
    for step in read_steps():
        if _already_present(step):
            continue
        prior = _prior_import(step)
        if not (prior and prior.status == "Success"):
            pending.append(step.step)
    return pending


def autoload():
    """after_install / after_migrate: queue the loader if anything is still missing."""
    try:
        if not frappe.conf.get("thinknxg_manufacturing_autoload", 1):
            return
        if "erpnext" not in frappe.get_installed_apps():
            return
        if not frappe.db.get_single_value("System Settings", "setup_complete"):
            return
        if not _pending():
            return
        frappe.enqueue(
            "thinknxg_manufacturing.demo.load",
            queue="long",
            timeout=7200,
            job_id=JOB_ID,
            deduplicate=True,
            enqueue_after_commit=True,
        )
    except Exception:
        frappe.log_error(title="KSSB demo autoload could not queue the loader")


@frappe.whitelist(methods=["POST"])
def start(retry_step=None):
    """Queue the loader by hand (System Manager)."""
    frappe.only_for("System Manager")
    frappe.enqueue(
        "thinknxg_manufacturing.demo.load",
        queue="long",
        timeout=7200,
        job_id=JOB_ID,
        deduplicate=True,
        retry_step=int(retry_step) if retry_step not in (None, "") else None,
    )
    return "queued"


@frappe.whitelist()
def status():
    """Per-step import state plus live record counts. Open in the browser as System Manager."""
    frappe.only_for("System Manager")
    steps = []
    for s in read_steps():
        prior = _prior_import(s)
        steps.append(
            {
                "step": s.step,
                "file": s.file,
                "doctype": s.doctype,
                "expected": s.docs,
                "state": "present on site" if _already_present(s) else (prior.status if prior else "not run"),
                "imported": _success_count(prior.name) if prior else 0,
                "data_import": prior.name if prior else None,
            }
        )
    counts = {
        dt: frappe.db.count(dt, {"docstatus": ["<", 2]})
        for dt in [
            "Item", "Workstation", "Operation", "BOM", "Supplier", "Customer", "Stock Reconciliation",
            "Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Quotation",
            "Sales Order", "Work Order", "Stock Entry", "Delivery Note", "Sales Invoice",
        ]
    }
    return {"complete": not _pending(), "pending_steps": _pending(), "steps": steps, "site_counts": counts}
