# P-055 CODEOWNERS Assistant — Start Here

Roadmap ID: **P-055**  
Candidate version: **0.10.0**  
State: **IN PROGRESS**

## What it does

CODEOWNERS can tell GitHub who should be requested to review changes to particular parts of a repository. Small mistakes in that file can silently change who gets requested or leave important ownership rules ineffective.

The DAIS CODEOWNERS Assistant gives you a **read-only local check** before you rely on a CODEOWNERS file. It:

- finds the effective local CODEOWNERS file using GitHub's documented search order;
- reports when lower-priority CODEOWNERS files are being ignored;
- flags several syntax forms that GitHub explicitly does not support;
- warns about repeated exact patterns where rule order matters;
- looks for an explicit rule that protects CODEOWNERS itself or its directory;
- produces deterministic privacy-minimized JSON evidence;
- produces the same technical status with an English or Spanish plain-language guide;
- never edits CODEOWNERS, never requests a reviewer, and never changes branch protection.

## GitHub Action

```yaml
- uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/codeowners-assistant@<released-version>
  with:
    root: .
    language: en
```

Until a versioned P-055 release exists, use the reviewed source/CI only; do not treat `main` as an immutable release reference.

## Local use

```bash
python scripts/p055_codeowners_assistant.py \
  --root /path/to/repository \
  --language en \
  --out-dir /tmp/p055-codeowners
```

The output directory must be outside the repository being audited.

## Status meanings

- `CODEOWNERS_MISSING` — no local CODEOWNERS exists in GitHub's documented locations.
- `CODEOWNERS_LOCAL_ERRORS` — the conservative local checks found an error.
- `CODEOWNERS_NEEDS_REVIEW` — no local error was found, but a warning still requires review.
- `CODEOWNERS_LOCAL_BASELINE_READY` — the bounded local checks passed without warnings.

None of those statuses means GitHub has verified owner identity, owner write access, branch protection, required code-owner review, complete repository coverage, or repository security.

## What to do with findings

1. Review the finding line number.
2. Check the actual repository owner/team access in GitHub.
3. Use GitHub's CODEOWNERS error UI/API for authoritative server-side syntax feedback.
4. Review rule order because later matching rules can change effective ownership.
5. Consider assigning ownership to CODEOWNERS itself and requiring code-owner review through branch protection or rulesets.

## Privacy

The retained JSON does not copy owner usernames, team names, or email addresses. Owner tokens are classified only by type and count; rule patterns are retained only as SHA-256 fingerprints. Do not paste credentials, secrets, private repository contents, or sensitive personal information into public support issues.

## Recovery

The product does not mutate the repository. Delete the generated output directory and rerun. If you later edit CODEOWNERS, use normal Git review/revert to recover those maintainer changes.
