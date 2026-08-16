# P-049 Secret Exposure Detection Action — Start Here

Status: **v0.6.0 release candidate — P-049 remains IN PROGRESS until governed release, released-ref acceptance, completion record and canonical synchronization pass.**

## What this product does

DAIS Secret Exposure Detection checks a bounded copy of your repository's **current working tree** for strings that Gitleaks identifies as secret-like material.

It is intentionally simple to consume:

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
    with:
      persist-credentials: false

  - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/secret-exposure-scan@v0.6.0
    with:
      root: .
```

`v0.6.0` does not exist until the governed release gate publishes it. Before that release, use only the exact reviewed source in this repository's own acceptance workflow.

## If the Action passes

A PASS means:

> Under the fixed P-049 policy, the pinned scanner reported no findings in the bounded working-tree files that were tested in that run.

A PASS **does not mean** that the repository contains no secrets. It does not scan Git history, validate credentials with providers, prove secrets were revoked, or establish that the repository is secure.

## If the Action fails with findings

The public log deliberately does **not** print the secret value, matching text, source path or raw Gitleaks report. It reports only that secret-like findings exist and how many were observed.

Treat that as an incident signal:

1. Do not paste the suspected value into a public issue, chat or CI log.
2. Inspect the repository locally in an authorized environment.
3. If the material is a real credential, revoke/rotate it at the issuing service first.
4. Remove the exposed material from the current source and address history separately if needed.
5. Re-run the Action after remediation.

Deleting a secret from the latest commit is not enough if the credential remains valid or exists in prior history.

## Why there is no `.gitleaks.toml` or `.gitleaksignore` customization input

Repository-controlled configuration can weaken a security gate. P-049 v0.6.0 therefore uses its own reviewed Gitleaks configuration and its own empty ignore file. Inline `gitleaks:allow` comments are also disabled.

This fixed-policy model is less flexible by design.

## Privacy

Raw scanner output can itself contain the secret. P-049 keeps that output only in temporary runner storage and deletes it after producing a sanitized result. Public evidence contains counts, rule IDs and SHA-256 fingerprints of non-secret finding metadata—not secret values, matched text or source paths.

## Supported environment

The v0.6.0 release candidate supports **GitHub-hosted Linux x64** only. Self-hosted runners are refused because untrusted repository content should not gain a filesystem/network oracle into private infrastructure.

## Need help?

Use the P-049 public issue form, but never include a credential, token, private key, full scanner finding, private repository content or private infrastructure detail in a public issue.
