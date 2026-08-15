# Universal Evidence real TUF refresh supporting acceptance

Status: **IN PROGRESS** — F-05 supporting acceptance, not completion  
Canonical foundation: **F-05 Universal Evidence Standard**

## Purpose

The earlier F-05 trusted-root work established local archival policy and network-isolated verification using retained trust material. A remaining gap was to prove a **real authenticated TUF client refresh from a historical root through current metadata**, plus verified `trusted_root.json` target retrieval through the Sigstore Public Good TUF repository.

This tranche adds that bounded hosted acceptance path. It runs only against public infrastructure from an ephemeral GitHub-hosted runner. It does not touch user devices, private DAIS infrastructure, production systems, credentials, or private data.

## Search before build

DAIS does not implement a competing TUF client.

- The Update Framework specification defines the authenticated metadata workflow, including root continuity, metadata versions, expiry checks, rollback resistance and freeze-attack defenses.
- `python-tuf` is the Python reference implementation and its `tuf.ngclient.Updater` implements the detailed top-level client refresh workflow.
- `securesystemslib` supplies signature/key support used by the TUF implementation. Its ECDSA/RSA cryptographic provider is an explicit `crypto` optional dependency backed by `cryptography`.
- Sigstore's `root-signing` repository maintains the TUF repository used to deliver Sigstore trust material to clients.
- GitHub CLI exposes `gh attestation trusted-root --verify-only` with an explicitly supplied out-of-band TUF root.

DAIS therefore contributes an **evidence and acceptance harness around upstream implementations**, not a new update-security protocol.

## Fail-honest dependency discovery

The first hosted attempts installed `tuf==7.0.0` without the optional `securesystemslib[crypto]` provider. Both historical root v5 and current root v15 then failed during bootstrap with:

```text
tuf.api.exceptions.UnsignedMetadataError: root was signed by 0/3 keys
```

The failures were retained and **not merged**. DAIS did not bypass signature verification, lower the signature threshold, patch metadata, or relabel the root as trusted.

Inspection of the upstream `securesystemslib` package metadata identified the missing dependency boundary: its `crypto` extra installs the `cryptography` provider required for these ECDSA signatures. The corrected acceptance therefore pins both:

```text
tuf==7.0.0
securesystemslib[crypto]==1.4.0
```

This is precisely why hosted acceptance exists: a seemingly valid TUF configuration must fail until the full verifier dependency contract is present.

## Historical bootstrap provenance

The corrected workflow returns to the historical Sigstore root version 5 from an immutable source revision:

```text
repository: sigstore/root-signing
commit: 54c142857637d12732de93a71adaadd0e561c749
path: metadata/root_history/5.root.json
Git blob SHA-1: 38f80f940473ac167abae3db9bc6a94d0bdb8c4e
expected TUF root version: 5
```

The Git blob identity is checked before the root is passed into the TUF client. The evidence output also records a SHA-256 of the exact bootstrap bytes used at run time.

Git object SHA-1 is used here only to bind the fetched bytes to the exact immutable Git object identified by GitHub. SHA-256 is retained separately as the evidence digest.

## Authenticated refresh path

The workflow passes the exact root-5 bytes through the explicit `bootstrap` argument to `tuf.ngclient.Updater`.

The acceptance succeeds only if:

1. the bootstrap bytes match the pinned Git blob identity;
2. the metadata is valid TUF root metadata at version 5;
3. `Updater.refresh()` completes against `https://tuf-repo-cdn.sigstore.dev/`;
4. the trusted root stored after refresh advances beyond version 5;
5. `trusted_root.json` is found through verified targets metadata;
6. `Updater.download_target()` downloads and verifies that target;
7. the verified target parses as a Sigstore TrustedRoot media type with non-empty CA, transparency-log and timestamp-authority sets;
8. sanitized evidence is emitted with exact client/library versions, bootstrap digest, refreshed root version, target digest and target size.

If successful, this truthfully shows that this exact upstream client and dependency set traversed an authenticated historical root-rotation path from v5 to the currently served root state during the run. It does not imply that every possible historical bootstrap, client, future rotation, or attack scenario is covered.

## Independent-tool supporting check

The hosted workflow also invokes GitHub CLI's `gh attestation trusted-root --verify-only` path using the same explicit root-5 bootstrap and Sigstore TUF repository URL.

A successful second-tool check is useful interoperability evidence. It is **not** an independent security audit and does not prove that every implementation handles every attack class correctly.

## Evidence truth boundary

The emitted acceptance record may truthfully state:

- this exact pinned python-tuf/securesystemslib toolchain accepted the exact immutable root-5 bootstrap;
- an authenticated historical root rotation was exercised by this exact client run;
- the top-level TUF refresh completed at run time;
- the exact downloaded `trusted_root.json` was verified against TUF target metadata;
- no user or production mutation occurred.

It must keep these claims false:

- every historical rotation path/client combination proven;
- future trusted-root freshness proven;
- future revocation awareness proven;
- every TUF attack class exercised;
- independent security review completed;
- artifact semantic goodness proven;
- production readiness proven;
- roadmap completion proven.

## Why this is not F-05 completion

This tranche closes an important real historical-root refresh gap if the hosted acceptance passes, but F-05 remains **IN PROGRESS**. Remaining completion work still includes explicit negative rollback/freeze fixtures through upstream clients, broader independent implementation coverage, reusable release/versioning, external standards/security review, real consumer/community acceptance, and canonical completion evidence.

No CI success in this file changes F-05 to COMPLETE.
