#!/usr/bin/env python3
"""
Boot gate (releasable invariant) verification script

Reads spec/run-profile.md (the run profile — human-finalized) and confirms "it builds and it boots"
deterministically. It is a mirror of the releasable state, not feature behavior judgment (E2E, demos).

Verdicts (fixed per type — deterministic):
  library:   the build command exits with code 0 within the time limit
  one-shot:  (after the build command succeeds) the boot command exits with code 0 within the time limit
  resident:  (after the build command succeeds) started with the boot command, the observation-check URL returns HTTP 2xx within the time limit
            — after confirming, it always cleans up with the stop command (if none, by terminating the process group)

Exit codes:
  0 = PASS. Without the profile file, 'not applicable' PASS — legacy/unfinalized projects behave unchanged (the same shape as the C3·C4 fallbacks)
  1 = FAIL — build/boot/observation failure (prints the output tail as evidence). It may be not a code defect but an environmental factor
      (a missing tool, an occupied port) — judging and remedying that belongs to the skill procedure; this script prints only facts
  2 = profile grammar error — the check was not performed (preventing a fake pass). Fix the notation to the template grammar and re-run

Usage:
    python3 scripts/verify_boot.py spec/run-profile.md

"""

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

# The fixed item names of the profile table (a closed list — in sync with run-profile-template.md)
FIELDS = ("Type", "Build command", "Boot command", "Observation check", "Time limit (s)", "Stop command")
TYPES = ("resident", "one-shot", "library")
NONE_VALUE = "None"
POLL_INTERVAL = 0.5  # resident observation polling interval (seconds)
TAIL_LINES = 15      # number of output-tail lines printed as FAIL evidence


def strip_md(cell):
    """Strip only the markdown decoration (backticks, bold) of a value cell — never touches the command content."""
    s = cell.strip()
    if s.startswith("**") and s.endswith("**") and len(s) >= 4:
        s = s[2:-2].strip()
    if s.startswith("`") and s.endswith("`") and len(s) >= 2:
        s = s[1:-1].strip()
    return s


def parse_profile(path):
    """Parse the profile table. Returns: (profile dict, list of grammar errors)."""
    profile = {}
    errors = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c for c in line.split("|")]
            # "| Item | Value |" → split gives [ '', ' Item ', ' Value ', '' ]
            if len(cells) < 4:
                continue
            key = strip_md(cells[1])
            value = strip_md(cells[2])
            if key in FIELDS:
                if key in profile:
                    errors.append(f"Item '{key}' is written more than once — write it only once.")
                profile[key] = value

    for field in FIELDS:
        if field not in profile:
            errors.append(f"Item '{field}' row is missing — the template's 6 item names are fixed.")
    if errors:
        return profile, errors

    # Value validation (closed rules — in sync with the template's 'success criteria per type')
    kind = profile["Type"]
    if kind not in TYPES:
        errors.append(f"Type '{kind}' is unknown — it must be one of {' / '.join(TYPES)}.")
    try:
        timeout = int(profile["Time limit (s)"])
        if timeout <= 0:
            raise ValueError
        profile["Time limit (s)"] = timeout
    except ValueError:
        errors.append(f"Time limit (s) '{profile['Time limit (s)']}' must be a positive integer.")
    for field in ("Build command", "Boot command", "Observation check", "Stop command"):
        if profile.get(field) == NONE_VALUE:
            profile[field] = None
        elif profile.get(field) == "":
            errors.append(f"Item '{field}' value is empty — if it does not apply, write '{NONE_VALUE}'.")
    if errors:
        return profile, errors

    if kind == "library":
        if not profile["Build command"]:
            errors.append("The library type requires a build command (the build is the only thing to confirm).")
    else:
        if not profile["Boot command"]:
            errors.append(f"The {kind} type requires a boot command.")
    if kind == "resident":
        url = profile["Observation check"]
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            errors.append("For the resident type, the observation check must be an http(s) URL.")
    return profile, errors


def tail_of(output_bytes):
    text = output_bytes.decode("utf-8", errors="replace") if output_bytes else ""
    lines = text.strip().splitlines()
    return lines[-TAIL_LINES:]


def print_fail(step, reason, output_bytes=None):
    print(f"FAIL — [{step}] {reason}")
    tail = tail_of(output_bytes)
    if tail:
        print(f"  Output tail (last {len(tail)} lines):")
        for line in tail:
            print(f"  | {line}")
    print("  (This may be an environmental factor, not a code defect — follow the skill procedure for judgment and remedy. No contorting to pass.)")


def run_step(step, cmd, timeout):
    """Run one command within the time limit. Returns: (success, output bytes)."""
    started = time.monotonic()
    try:
        result = subprocess.run(
            cmd, shell=True, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
    except subprocess.TimeoutExpired as e:
        print_fail(step, f"did not finish within the {timeout}s time limit: {cmd}", e.output)
        return False, e.output or b""
    elapsed = time.monotonic() - started
    if result.returncode != 0:
        print_fail(step, f"exit code {result.returncode} (expected 0): {cmd}", result.stdout)
        return False, result.stdout
    print(f"  [{step}] OK — exit code 0 ({elapsed:.1f}s): {cmd}")
    return True, result.stdout


def terminate_process(proc, stop_cmd):
    """Always clean up a resident process — the stop command (if any), then process-group termination."""
    if stop_cmd:
        try:
            subprocess.run(stop_cmd, shell=True, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass  # the process termination below still guarantees the cleanup
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (AttributeError, OSError, ProcessLookupError):
        proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (AttributeError, OSError, ProcessLookupError):
            proc.kill()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass


def check_resident(profile):
    """Resident: start it with the boot command and wait for HTTP 2xx from the observation URL within the time limit."""
    cmd = profile["Boot command"]
    url = profile["Observation check"]
    timeout = profile["Time limit (s)"]
    try:
        proc = subprocess.Popen(
            cmd, shell=True, start_new_session=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
    except OSError as e:
        print_fail("boot", f"could not start the command: {e}")
        return False
    started = time.monotonic()
    try:
        while time.monotonic() - started < timeout:
            if proc.poll() is not None:
                output = proc.stdout.read() if proc.stdout else b""
                print_fail("boot", f"resident type, but the process ended first with exit code {proc.returncode}: {cmd}", output)
                return False
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    status = resp.status
                if 200 <= status < 300:
                    elapsed = time.monotonic() - started
                    print(f"  [boot] OK — process resident: {cmd}")
                    print(f"  [observation] OK — {url} → HTTP {status} ({elapsed:.1f}s)")
                    return True
            except (urllib.error.URLError, OSError, ValueError):
                pass  # not ready yet — retry until the time limit
            time.sleep(POLL_INTERVAL)
        print_fail("observation", f"{url} did not respond with HTTP 2xx within the {timeout}s time limit.")
        return False
    finally:
        terminate_process(proc, profile["Stop command"])


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/verify_boot.py spec/run-profile.md")
        return 2
    path = sys.argv[1]
    print("=" * 60)
    print("Boot gate — releasable invariant (does it build and boot)")
    print("=" * 60)

    if not os.path.isfile(path):
        print(f"✅ PASS — not applicable: there is no run profile ({path}).")
        print("  (The profile is finalized by human approval in the scaffolding-completion report — before finalization and in legacy projects, nothing is checked.)")
        return 0

    profile, errors = parse_profile(path)
    if errors:
        print(f"⚠️ {len(errors)} profile grammar error(s) — the check was not performed (preventing a fake pass):")
        for err in errors:
            print(f"  ⚠️ {err}")
        print("  → Fix only the notation to run-profile-template.md's machine-readable grammar and re-run (value changes go through human re-finalization).")
        return 2

    kind = profile["Type"]
    timeout = profile["Time limit (s)"]
    print(f"  Profile: type={kind} · time limit={timeout}s · target={path}")

    if profile["Build command"]:
        ok, _ = run_step("build", profile["Build command"], timeout)
        if not ok:
            return 1
    if kind == "library":
        pass  # for the library type, build success is the verdict itself
    elif kind == "one-shot":
        ok, _ = run_step("boot", profile["Boot command"], timeout)
        if not ok:
            return 1
    else:  # resident
        if not check_resident(profile):
            return 1

    print("✅ PASS — releasable invariant holds: it builds and it boots (behavior judgment is outside this gate).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
