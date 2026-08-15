# Universal Evidence real TUF refresh supporting acceptance

Status: **IN PROGRESS** — F-05 supporting acceptance, not completion  
Canonical foundation: **F-05 Universal Evidence Standard**

## Purpose

The earlier F-05 trusted-root work established local archival policy and network-isolated verification using retained trust material. A remaining gap was to prove a **real authenticated TUF client refresh** from an explicitly pinned historical trust root through the currently published Sigstore Public Good TUF repository, rather than treating a downloaded `trusted_root.json` file as trusted merely because it came from HTTPS.

This tranche adds that bounded hosted acceptance path. It runs only against public infrastructure from an ephemeral GitHub-hosted runner. It does not touch user devices, private DAIS infrastructure, production systems, credentials, or private data.

## Search before build

DAIS does not implement a competing TUF client.

- The Update Framework specification defines the authenticated metadata workflow, including root continuity, metadata versions, expiry checks, rollback resistance, and freeze-attack detection semantics.
- `python-tuf` is the Python reference implementation and its `tuf.ngclient.Updater` implements the detailed top-level client refresh workflow.
- Sigstore's `root-signing` repository maintains the TUF repository used to deliver the Sigstore trust root to clients.
- Sigstore documentation identifies root version 5 as a compatible historical bootstrap point for current client implementations after an earlier key-encoding transition.
- GitHub CLI exposes `gh attestation trusted-root --verify-only` for verifying a TUF trusted-root repository using an explicitly supplied out-of-band root.

DAIS therefore contributes an **evidence and acceptance harness around upstream implementations**, not a new update-security protocol.

## Pinned bootstrap provenance

The hosted acceptance obtains Sigstore root version 5 from an immutable source revision:

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

The workflow uses pinned `python-tuf==7.0.0` and passes the exact root-5 bytes through the required `bootstrap` argument to `tuf.ngclient.Updater`.

The acceptance succeeds only if:

1. the bootstrap bytes match the pinned Git blob identity;
2. the metadata is valid TUF root metadata at version 5;
3. `Updater.refresh()` completes against `https://tuf-repo-cdn.sigstore.dev/`;
4. the trusted root stored after refresh has advanced beyond version 5;
5. `trusted_root.json` is found through verified targets metadata;
6. `Updater.download_target()` downloads and verifies that target;
7. the verified target parses as a Sigstore TrustedRoot media type with non-empty CA, transparency-log, and timestamp-authority sets;
8. sanitized evidence is emitted with exact client version, bootstrap digest, refreshed root version, target digest and target size.

## Independent-tool supporting check

The hosted workflow also invokes GitHub CLI's independent `gh attestation trusted-root --verify-only` path using the same explicit bootstrap root and Sigstore TUF repository URL.

A successful second-tool check is useful interoperability evidence. It is **not** an independent security audit and does not prove that every client implementation handles every attack class correctly.

## Evidence truth boundary

The emitted acceptance record may truthfully state:

- this exact python-tuf client version authenticated a root chain starting from the pinned bootstrap;
- the top-level TUF refresh completed at run time;
- the root version advanced beyond the historical bootstrap;
- the exact downloaded `trusted_root.json` was verified against TUF target metadata;
- no user or production mutation occurred.

It must keep these claims false:

- future trusted-root freshness proven;
- future revocation awareness proven;
- every TUF attack class exercised;
- independent security review completed;
- artifact semantic goodness proven;
- production readiness proven;
- roadmap completion proven.

## Why this is not F-05 completion

This tranche closes an important real-client refresh gap but F-05 remains **IN PROGRESS**. Remaining completion work still includes broader multi-snapshot/rotation acceptance, explicit negative rollback/freeze fixtures through an upstream TUF client, stronger independent implementation coverage, reusable release/versioning, external standards/security review, real consumer/community acceptance, and canonical completion evidence.

No CI success in this file changes F-05 to COMPLETE.
