# P-058 Dangerous-Script Detector — Start Here

**Status:** product candidate (`IN_PROGRESS`)  
**Version:** 0.12.0  
**Purpose:** tell a maintainer when a script contains execution or mutation patterns that deserve explicit review **without executing the script**.

## Use it in GitHub Actions

```yaml
- uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/dangerous-script-detector@<reviewed-ref>
  with:
    root: .
```

The Action scans supported script files and GitHub workflow/action YAML. It is deliberately static and non-executing.

### Result meanings

- `PASS`: no configured dangerous-pattern rule matched.
- `REVIEW_REQUIRED`: one or more rules matched.
- HIGH or CRITICAL findings fail the Action.
- MEDIUM findings are retained for review but do not automatically fail the Action.
- `ERROR`: the input could not be scanned within the safety boundary, so the run fails closed.

**PASS does not mean a script is safe.** It means only that this exact detector did not match its bounded rule set.

## What it scans

Supported text files:

- `sh`, `bash`, `zsh`, `ksh`
- PowerShell `ps1` / `psm1`
- Windows `bat` / `cmd`
- `.github/workflows/*.yml|yaml`
- `action.yml` / `action.yaml`

It refuses unsafe root traversal and script/config symlinks, limits file/aggregate size, never executes repository code, never opens the network, and writes only a runner-temporary sanitized JSON report.

## Findings are privacy-minimized

Retained findings contain rule ID, severity, category, language, line number, and SHA-256 fingerprints for the relative path and source line. They do **not** retain the matched line, absolute path, command text, credential value, stdout, or stderr.

## If the Action fails

1. Treat the finding as a review signal, not automatic proof of malicious intent.
2. Inspect the exact source privately.
3. Determine whether the operation is required, bounded, reversible, and explicitly authorized.
4. Prefer a safer native mechanism where available.
5. Re-run after the source is changed or the risk is explicitly handled outside this detector.

Do not suppress a finding by weakening this Action. If a rule is materially wrong, open the P-058 support form with a sanitized reproducer.
