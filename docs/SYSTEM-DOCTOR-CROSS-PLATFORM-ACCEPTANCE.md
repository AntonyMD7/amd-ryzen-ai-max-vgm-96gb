# Universal System Doctor cross-platform hosted acceptance

**Foundation:** F-02 Universal System Doctor — **IN PROGRESS**.

This tranche exercises the same privacy-minimizing, read-only System Doctor contract on GitHub-hosted Ubuntu, Windows and macOS runners. It closes a hosted operating-system portability gap without pretending that disposable cloud runners are representative physical hardware diagnostics.

## Why hosted OS acceptance

The baseline collector is intentionally conservative and uses Python standard-library mechanisms with a small Windows-specific memory adapter. Before adding more vendor/hardware adapters, the common report, privacy, storage, tool-presence and accessible-rendering contracts should behave consistently across the major desktop/server operating-system families.

GitHub's current standard hosted-runner labels include `ubuntu-24.04`, `windows-2025` and `macos-15`, so the workflow uses those explicit images rather than relying on moving `*-latest` labels.

## Acceptance contract

For each hosted environment, the harness:

1. runs the existing System Doctor collector;
2. validates the report against the existing JSON Schema;
3. requires `READ_ONLY` collector mode;
4. requires every privacy and mutation flag to remain `false`;
5. renders the same report truth in English and Spanish;
6. verifies the static semantic/report accessibility contract;
7. records exact SHA-256 digests for report and HTML artifacts;
8. records the observed OS/release/architecture/Python fields already allowed by the public report contract;
9. uploads only the sanitized report/render/evidence artifacts.

## Claim boundary

A matrix PASS means the bounded **hosted OS contract was exercised** on that specific runner image.

It does **not** establish:

- physical hardware health;
- OEM firmware or BIOS correctness;
- GPU/NPU/accelerator health;
- vendor-driver correctness;
- peripheral compatibility;
- comprehensive fault diagnosis;
- WCAG conformance or real assistive-technology usability;
- production readiness.

Those remain separate adapters and acceptance gates.

## Privacy boundary

The common collector deliberately excludes username, hostname, network addresses, environment values, credentials, user files and process command lines. The hosted acceptance layer adds no new collection of those fields.

## Remaining F-02 completion gates

F-02 remains **IN PROGRESS** after this tranche. The canonical completion contract still requires, among other applicable gates:

- dedicated reusable distribution/release;
- representative real physical Windows/Linux/macOS acceptance rather than hosted images alone;
- bounded vendor/hardware adapters with their own evidence and rollback/non-mutation boundaries;
- broader error/recovery UX and beginner validation;
- independent security/privacy/accessibility review;
- versioned release/tag and retained canonical completion evidence.
