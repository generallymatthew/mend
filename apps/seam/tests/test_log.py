"""Shared helper for sweep scripts to append a human-readable run record to
TEST_LOG.md: which prompt (and git state) was tested, every scenario run,
and the result -- including scenarios that didn't behave as expected, not
just a pass/fail summary. The point is a continuous record across prompt
iterations (for Seam and, via the mirrored copy, Thimble), not a single
latest-run snapshot -- so it only ever appends, never overwrites.

"Expected to trip" is inferred from the scenario's own category label by
convention, not a separate field on each scenario tuple: any category
containing "no floor" or "non-floor" is expected to stay quiet, everything
else is expected to trip. This matches the naming convention every sweep
file in this repo already uses.
"""
import datetime
import subprocess


def git_info(path):
    """Short hash + clean/dirty for a single file, so a log entry can be
    matched back to the exact prompt text that produced it."""
    try:
        h = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", str(path)],
            capture_output=True, text=True, cwd=path.parent,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", str(path)],
            capture_output=True, text=True, cwd=path.parent,
        ).stdout.strip()
        return (h or "unknown"), ("dirty" if dirty else "clean")
    except Exception:
        return "unknown", "unknown"


def expected_to_trip(category):
    c = category.lower()
    return not ("no floor" in c or "non-floor" in c)


def append_log(log_path, script_name, prompt_paths, repeats, rows):
    """rows: list of (category, name, trips, total, errors, seen) tuples,
    one per scenario, as accumulated by the sweep's own main loop. `errors`
    is the count of repeats that raised (e.g. the server dropped mid-run)
    rather than returning a real answer -- those never count toward a trip
    rate or a failure verdict, so a crashed server can't get silently
    logged as "the model missed this harassment case." A scenario where
    every repeat errored gets its own ERROR row instead of a 0/N rate."""
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"\n## {ts} -- {script_name}", ""]
    for p in prompt_paths:
        h, status = git_info(p)
        lines.append(f"**Prompt:** `{p.name}` @ `{h}` ({status})")
    lines.append(f"**Repeats:** {repeats}")
    lines.append("")
    lines.append("| Category | Scenario | Trip rate | Categories seen |")
    lines.append("|---|---|---|---|")

    failures = []
    errored = []
    for category, name, trips, total, errors, seen in rows:
        completed = total - errors
        if completed <= 0:
            lines.append(f"| {category} | {name} | ERROR ({errors}/{total} failed) | -- |")
            errored.append((category, name, errors, total))
            continue

        rate = f"{trips}/{completed}"
        if errors:
            rate += f" ({errors} error{'s' if errors != 1 else ''})"
        exp = expected_to_trip(category)
        flag = ""
        if exp and trips == 0:
            flag = " ⚠️"
            failures.append((category, name, rate, "expected to trip, did not"))
        elif not exp and trips > 0:
            flag = " ⚠️"
            failures.append((category, name, rate, "expected NOT to trip, did"))
        lines.append(f"| {category} | {name} | {rate}{flag} | {seen} |")

    lines.append("")
    if failures:
        lines.append("**Failures:**")
        for category, name, rate, why in failures:
            lines.append(f"- {category} -- {name} -- {rate} -- {why}")
    else:
        lines.append("**Failures:** none")

    if errored:
        lines.append("")
        lines.append("**Errored (no real result -- rerun, don't treat as a finding):**")
        for category, name, errors, total in errored:
            lines.append(f"- {category} -- {name} -- {errors}/{total} attempts failed")
    lines.append("")

    text = "\n".join(lines)
    with open(log_path, "a") as f:
        f.write(text + "\n")
    return text
