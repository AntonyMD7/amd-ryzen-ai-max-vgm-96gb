# Universal Evidence real TUF refresh supporting acceptance

Status: **IN PROGRESS** — F-05 supporting acceptance, not completion  
Canonical foundation: **F-05 Universal Evidence Standard**

## Purpose

The earlier F-05 trusted-root work established local archival policy and network-isolated verification using retained trust material. A remaining gap was to prove a **real authenticated TUF client refresh** and verified `trusted_root.json` target through the Sigstore Public Good TUF repository, rather than treating a downloaded trust-root file as trusted merely because it came from HTTPS.

This tranche adds that bounded hosted acceptance path. It runs only against public infrastructure from an ephemeral GitHub-hosted runner. It does not touch user devices, private DAIS infrastructure, production systems, credentials, or private data.

## Search before build

DAIS does not implement a competing TUF client.

- The Update Framework specification defines the authenticated metadata workflow, including trusted-root handling, metadata versions, expiry checks, rollback resistance and freeze-attack defenses.
- `python-tuf` is the Python reference implementation; its `tuf.ngclient.Updater` implements the detailed top-level client refresh workflow.
- Sigstore's `root-signing` repository maintains the TUF repository used to deliver Sigstore trust material to clients.
- GitHub CLI exposes `gh attestation trusted-root --verify-only` with an explicitly supplied out-of-band TUF root.

DAIS therefore contributes an **evidence and acceptance harness around upstream implementations**, not a new update-security protocol.

## Fail-honest bootstrap discovery

The first hosted attempt deliberately tried the historical Sigstore root version 5 because older Sigstore guidance identified that point as a compatibility boundary after an earlier ECDSA-key encoding transition. The exact source was:

```text
repository: sigstore/root-signing
commit: 54c142857637d12732de93a71adaadd0e561c749
path: metadata/root_history/5.root.json
Git blob SHA-1: 38f80f940473ac167abae3db9bc6a94d0bdb8c4e
expected TUF root version: 5
```

Pinned `python-tuf==7.0.0` rejected that bootstrap with `UnsignedMetadataError: root was signed by 0/3 keys`. The workflow failed and was **not** merged. DAIS did not bypass signature verification, weaken thresholds, or re-label the bytes as trusted.

That negative result is retained as an interoperability finding: historical root-5 bootstrap compatibility must not be assumed for this current client/toolchain.

## Current pinned bootstrap provenance

The corrected hosted acceptance uses the current root at the same immutable `sigstore/root-signing` commit:

```text
repository: sigstore/root-signing
commit: 54c142857637d12732de93a71adaadd0e561c749
path: metadata/root.json
Git blob SHA-1: 55115df1025e64a6be12548bb1a1fa09451fc7f4
expected TUF root version: 15
```

The Git blob identity is checked before the root is passed into the TUF client. The evidence output also records a SHA-256 of the exact bootstrap bytes used at run time.

Git object SHA-1 is used here only to bind the fetched bytes to the exact immutable Git object identified by GitHub. SHA-256 is retained separately as the evidence digest.

## Authenticated refresh path

The workflow uses pinned `python-tuf==7.0.0` and passes the exact root-15 bytes through the explicit `bootstrap` argument to `tuf.ngclient.Updater`.

The acceptance succeeds only if:

1. the bootstrap bytes match the pinned Git blob identity;
2. the metadata is valid TUF root metadata at version 15;
3. `Updater.refresh()` completes against `https://tuf-repo-cdn.sigstore.dev/`;
4. the trusted root stored after refresh does not regress below the pinned bootstrap version;
5. `trusted_root.json` is found through verified targets metadata;
6. `Updater.download_target()` downloads and verifies that target;
7. the verified target parses as a Sigstore TrustedRoot media type with non-empty CA, transparency-log and timestamp-authority sets;
8. sanitized evidence is emitted with exact client version, bootstrap digest, refreshed root version, target digest and target size.

Because the bootstrap is the current root, this acceptance intentionally does **not** claim that a historical multi-root rotation was exercised. That remains a separate F-05 gap.

## Independent-tool supporting check

The hosted workflow also invokes GitHub CLI's `gh attestation trusted-root --verify-only` path using the same explicit current bootstrap root and Sigstore TUF repository URL.

A successful second-tool check is useful interoperability evidence. It is **not** an independent security audit and does not prove that every implementation handles every attack class correctly.

## Evidence truth boundary

The emitted acceptance record may truthfully state:

- this exact python-tuf client version accepted the explicitly pinned current root;
- the top-level TUF refresh completed at run time;
- trusted root state did not regress below the pinned version;
- the exact downloaded `trusted_root.json` was verified against TUF target metadata;
- no user or production mutation occurred.

It must keep these claims false:

- historical multi-root rotation proven;
- future trusted-root freshness proven;
- future revocation awareness proven;
- every TUF attack class exercised;
- independent security review completed;
- artifact semantic goodness proven;
- production readiness proven;
- roadmap completion proven.

## Why this is not F-05 completion

This tranche closes a real authenticated-current-root refresh gap and records a useful historical-bootstrap incompatibility, but F-05 remains **IN PROGRESS**. Remaining completion work still includes authenticated historical/multi-snapshot rotation acceptance with a compatible upstream client, explicit negative rollback/freeze fixtures, stronger independent implementation coverage, reusable release/versioning, external standards/security review, real consumer/community acceptance, and canonical completion evidence.

No CI success in this file changes F-05 to COMPLETE.
