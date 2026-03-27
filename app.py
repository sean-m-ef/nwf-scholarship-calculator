import marimo

__generated_with = "0.21.1"
app = marimo.App(width="medium", app_title="NWF Scholarship Calculator")


@app.cell
def _imports():
    import marimo as mo
    return (mo,)


@app.cell
def _header(mo):
    mo.md("""
    # Nevada Women's Fund — Scholarship Distribution Engine

    Upload the recipients and scholarships CSV files, set the minimum split threshold, then click **Run Solver**.
    """)
    return


@app.cell
def _controls(mo):
    recipients_upload = mo.ui.file(label="Recipients CSV", filetypes=[".csv"])
    scholarships_upload = mo.ui.file(label="Scholarships CSV", filetypes=[".csv"])
    min_split = mo.ui.number(value=100, start=0, stop=10000, step=50, label="Minimum split amount ($)")
    run_button = mo.ui.run_button(label="Run Solver")
    return min_split, recipients_upload, run_button, scholarships_upload


@app.cell
def _upload_ui(mo, min_split, recipients_upload, run_button, scholarships_upload):
    mo.vstack([
        mo.hstack([recipients_upload, scholarships_upload], justify="start", gap=2),
        min_split,
        run_button,
    ])
    return


@app.cell
def _load_data(mo, recipients_upload, scholarships_upload):
    from engine.loader import load_recipients, load_scholarships, validate_balance

    if not recipients_upload.value or not scholarships_upload.value:
        mo.stop(True, mo.callout(mo.md("Upload both CSV files to continue."), kind="warn"))

    recip_bytes = recipients_upload.value[0].contents
    schol_bytes = scholarships_upload.value[0].contents

    try:
        recipients = load_recipients(recip_bytes)
        scholarships, criteria, load_warnings = load_scholarships(schol_bytes)
    except ValueError as e:
        mo.stop(True, mo.callout(mo.md(f"**Load error:** {e}"), kind="danger"))

    balance = validate_balance(recipients, scholarships)
    return balance, criteria, load_warnings, recipients, scholarships


@app.cell
def _data_summary(mo, balance, load_warnings, recipients, scholarships):
    lines = [
        f"**Recipients loaded:** {len(recipients)}  |  **Total awards:** ${recipients['award_amount'].sum():,.2f}",
        f"**Scholarships loaded:** {len(scholarships)}  |  **Total pool:** ${scholarships['amount'].sum():,.2f}",
    ]
    if balance["balanced"]:
        lines.append("✓ Pool and awards are balanced.")
    else:
        delta = balance["delta"]
        lines.append(f"⚠ Pool and awards differ by **${delta:+,.2f}**. Results may be incomplete.")

    if load_warnings:
        for w in load_warnings:
            lines.append(f"⚠ {w}")

    mo.callout(mo.md("\n\n".join(lines)), kind="info")
    return


@app.cell
def _eligibility_matrix(mo, criteria, recipients, scholarships):
    from engine.eligibility import build_matrix, summarize_coverage

    matrix = build_matrix(recipients, scholarships, criteria)
    coverage = summarize_coverage(matrix)

    blocked = coverage["recipients_with_zero_eligibility"]
    if blocked:
        mo.stop(
            True,
            mo.callout(
                mo.md(f"**{len(blocked)} recipient(s) qualify for zero scholarships** and cannot be funded: {', '.join(blocked)}. Fix eligibility criteria before solving."),
                kind="danger",
            ),
        )

    return coverage, matrix


@app.cell
def _coverage_summary(mo, coverage):
    rps = coverage["scholarships_per_recipient"]
    min_s = coverage["min_scholarships_per_recipient"]
    max_s = coverage["max_scholarships_per_recipient"]
    avg_s = sum(rps.values()) / len(rps) if rps else 0
    mo.callout(
        mo.md(f"**Eligibility coverage:** each recipient qualifies for {min_s}–{max_s} scholarships (avg {avg_s:.1f})"),
        kind="success",
    )
    return


@app.cell
def _solve(mo, matrix, min_split, recipients, run_button, scholarships):
    from engine.solver import solve
    from engine.postprocess import process

    mo.stop(not run_button.value)

    with mo.status.spinner(title="Running solver…"):
        result = solve(recipients, scholarships, matrix, timeout_seconds=120)
        processed = process(result, recipients, scholarships, min_split_amount=min_split.value)

    return processed, result


@app.cell
def _solve_status(mo, processed, result):
    if result.status == "Optimal":
        n_infeasible = len(result.infeasible_recipients)
        n_small = processed.allocations["small_split"].sum() if not processed.allocations.empty else 0
        msg = f"✓ **Solve complete** in {result.solve_time_s:.2f}s  |  {len(processed.recipient_summary)} recipients  |  {len(processed.allocations)} allocations"
        if n_infeasible:
            msg += f"  |  ⚠ **{n_infeasible} infeasible** (see Recipient Summary)"
        if n_small:
            msg += f"  |  ⚠ **{n_small} small split(s)** below minimum"
        kind = "warn" if (n_infeasible or n_small) else "success"
    else:
        msg = f"✗ **Solver status: {result.status}** — {result.message}"
        kind = "danger"

    mo.callout(mo.md(msg), kind=kind)
    return


@app.cell
def _results_tables(mo, processed, result):
    mo.stop(result.status != "Optimal")

    alloc_display = processed.allocations.drop(columns=["small_split"]).rename(columns={
        "recipient_id": "Recipient ID",
        "recipient_name": "Recipient",
        "scholarship_id": "Scholarship ID",
        "scholarship_name": "Scholarship",
        "amount": "Amount ($)",
    })

    mo.vstack([
        mo.md("### Allocations"),
        mo.ui.table(alloc_display),
    ])
    return


@app.cell
def _download(mo, processed, result):
    from engine.exporter import build_excel

    mo.stop(result.status != "Optimal")

    excel_bytes = build_excel(processed)

    mo.vstack([
        mo.md("### Download Results"),
        mo.download(
            data=excel_bytes,
            filename="nwf_allocations.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            label="Download Excel",
        ),
    ])
    return


if __name__ == "__main__":
    app.run()
