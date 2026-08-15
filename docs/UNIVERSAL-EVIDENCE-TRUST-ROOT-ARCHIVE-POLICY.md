# Universal Evidence — trusted-root archive and refresh policy v0.1

**Roadmap mapping:** F-05 Universal Evidence Standard; supports P-050, P-212, P-213 and P-224.  
**State:** IN PROGRESS policy/supporting evidence only.

## Purpose

The preceding network-isolated acceptance proved a narrow property: an exact public artifact and Sigstore bundle can be verified with an explicit frozen TrustedRoot while the verifier has no external route. That deliberately left a more important operational question open: how should an offline environment record, age, chain and reject stale trusted-root snapshots without inventing another PKI?

This tranche adds a small, machine-checkable archival record and local refresh-window evaluator. It does **not** become a trust root, TUF client, revocation service or cryptographic verifier.

## Search-before-build

The design continues to adopt existing upstream mechanisms rather than replace them:

- Sigstore's `TrustedRoot` protocol object is the canonical container for trusted verification material; its population may come from TUF or files on disk.
- Sigstore's public-good root is distributed through the existing `sigstore/root-signing` TUF repository.
- Cosign supports explicit TrustedRoot material for verification, including offline verification workflows.
- The Update Framework (TUF) already defines authenticated metadata versioning, expiry and root-update rules; DAIS therefore does not invent a root-signing or root-rotation protocol.

The new DAIS record exists only to retain **local archival provenance and a fail-closed refresh deadline around an upstream root snapshot**.

## Artifacts

- `schemas/trusted-root-snapshot-v0.1.schema.json` — strict public metadata shape.
- `scripts/trusted_root_snapshot_policy.py` — deterministic local policy evaluator.
- `examples/trusted-root-snapshot-synthetic-v0.1.json` — synthetic/non-authoritative example.
- `tests/test_trusted_root_snapshot_policy.py` — positive and negative contract tests.

## Record contents

A snapshot record captures only public/non-secret metadata:

```text
snapshot id
upstream ecosystem + retrieval method + HTTPS source URI
UTC acquisition time
TrustedRoot media type + exact SHA-256 + byte size
CA / transparency-log / timestamp-authority counts
verifier name + concrete version
maximum local age + explicit refresh due time
optional SHA-256 link to the previous snapshot record
offline-import approval as a recorded boolean
explicit false truth/completion claims
```

The schema and evaluator reject embedded URI credentials and require all semantic/completion claims to remain false.

## Deterministic evaluation

The CLI requires an explicit `--as-of` UTC time instead of silently reading the system clock:

```bash
python scripts/trusted_root_snapshot_policy.py \
  examples/trusted-root-snapshot-synthetic-v0.1.json \
  --as-of 2026-08-15T12:00:00Z
```

Before the declared local deadline, a structurally valid record can report:

```text
ARCHIVE_POLICY_SATISFIED
WITHIN_LOCAL_REFRESH_WINDOW
```

After that deadline it fails closed with:

```text
ARCHIVE_POLICY_REJECTED
LOCAL_REFRESH_OVERDUE
```

These labels describe only the **local archival policy**. They never mean that upstream TUF metadata is currently valid or that the TrustedRoot remains globally current.

## Optional previous-snapshot hash link

A record may declare `previous_snapshot_record_sha256`. When the exact previous record bytes are supplied, the evaluator hashes those bytes and reports `VERIFIED` or `MISMATCH`. A mismatch rejects the archival policy.

This is an append-only evidence aid, not a blockchain, transparency log, signature scheme or anti-rollback proof. A malicious party able to rewrite an entire unanchored archive could rewrite the links too. Stronger archival integrity requires an authenticated external anchor or signed transparency mechanism.

## Deliberate truth boundary

Even a green result keeps all of these claims false:

- TUF metadata verified by this module;
- TrustedRoot current globally;
- future revocation awareness;
- cryptography performed;
- network contact performed;
- artifact goodness;
- semantic truth;
- production readiness;
- roadmap completion.

The policy evaluator also does not interpret `offline_import_approved=true` as proof that a human approval actually occurred. It merely preserves the supplied record. Real approval evidence belongs in a separately governed system.

## Safety and privacy

The record is designed for public trust metadata only. It must not contain OIDC tokens, private keys, bearer tokens, internal hostnames, private repository paths, user/device identifiers or private infrastructure detail. The source URI must be HTTPS and cannot contain embedded username/password credentials.

## What this advances

This closes one portion of the previously explicit F-05 gap by making root-snapshot age and record-chain handling deterministic and testable. It also gives future offline-verification tooling a narrow failure boundary: an expired local snapshot can be rejected before an artifact trust decision is attempted.

## What remains before F-05 completion

F-05 remains **IN PROGRESS**. Remaining gates include, at minimum:

1. exercise a real multi-snapshot refresh/import lifecycle over time using authenticated upstream TUF metadata;
2. demonstrate rollback/freeze resistance through the upstream TUF client rather than local timestamps alone;
3. independent implementation interoperability using a second verifier/toolchain;
4. independent security review of the builder/verifier/trust model;
5. dedicated reusable distribution, versioning and release lifecycle;
6. representative external/community use and feedback;
7. full canonical completion evidence.

No item in this tranche satisfies those gates by itself.
