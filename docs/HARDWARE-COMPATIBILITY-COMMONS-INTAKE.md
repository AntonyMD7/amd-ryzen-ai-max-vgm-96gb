# Hardware Compatibility Commons Public Intake v0.2

Status: **IN PROGRESS — public evidence intake contract, not a compatibility guarantee**

Canonical roadmap mapping: **F-04 Hardware Compatibility Commons**, supporting P-008/P-011/P-012/P-013/P-014/P-015 and the infrastructure/evidence tranche.

## Why this tranche exists

The Commons needs community evidence, but “upload the whole diagnostic log” is the wrong default for a public-good repository. Raw probes can contain hostnames, usernames, private network addresses, serial numbers, MAC addresses, home-directory paths, tokens, or other identifiers that are unnecessary for most compatibility questions.

The v0.2 intake contract therefore separates:

- the **minimum technical configuration needed to reproduce an observation**;
- the **evidence needed to justify the observation state**;
- the **provenance/review state**;
- the **privacy assertions required before public review**;
- the things the intake validator itself can and cannot prove.

## Search-before-build / upstream boundary

The Hardware Compatibility Commons should interoperate with mature upstream ecosystems instead of cloning their collectors or update systems.

- **Linux Hardware Project / hw-probe** already probes hardware, checks operability, helps find drivers, and contributes to a community hardware database. Linux-specific future adapters should be able to reference or import *reviewed/sanitized* hw-probe evidence instead of inventing a parallel full-machine probe: https://github.com/linuxhw/hw-probe
- **fwupd + LVFS** already provide firmware discovery/update infrastructure, metadata, testing, and optional success/failure reporting. Firmware compatibility records should link to exact firmware/LVFS evidence where appropriate rather than implementing a second public firmware updater: https://github.com/fwupd/fwupd and https://lvfs.readthedocs.io/
- LVFS documents that update telemetry/report upload is optional/user-mediated. The Commons should keep contribution consent explicit and should never turn compatibility intake into silent telemetry: https://lvfs.readthedocs.io/en/latest/telemetry.html

The DAIS Commons contributes a cross-project **public evidence vocabulary, privacy prefilter, claim-integrity rules, and versioned reproduction record**. It is not the authoritative vendor driver database and it is not a firmware deployment service.

## v0.2 public report surface

`schemas/hardware-compatibility-report-v0.2.schema.json` deliberately excludes raw logs and arbitrary nested configuration objects. A report contains only:

- bounded hardware/product-family facts;
- exact software/driver/runtime/firmware version strings when relevant;
- a small list of public technical configuration key/value pairs;
- a bounded outcome state and reproduction count;
- evidence method, hashes, public HTTPS references and bounded reproduction steps;
- reporter class and review state;
- explicit privacy declarations;
- explicit non-guarantee claims;
- limitations.

The older v0.1 schema remains available for historical continuity; v0.2 is the preferred public-intake contract for new Commons work.

## Claim-integrity rules

`hardware_compatibility_intake.py` adds semantic rules that are intentionally stricter than JSON shape validation.

A `VERIFIED_WORKING` or `VERIFIED_FAILING` outcome requires:

- evidence method `REPRODUCIBLE_TEST`;
- at least one reproduction run;
- at least one SHA-256 artifact digest;
- a review state other than `UNREVIEWED`.

Vendor documentation alone and community testimony alone cannot become an observed verified outcome. A CI-generated synthetic record cannot claim a real-hardware outcome.

Even a report that satisfies those rules is returned only as:

`ELIGIBLE_FOR_PUBLIC_REVIEW_NOT_VERIFIED`

The validator never sets `compatibility_verified_by_intake=true`. Schema/privacy/claim checks are not equivalent to independent reproduction.

## Privacy prefilter

Before public review, the intake validator refuses likely:

- private-key material;
- common GitHub/API/AWS/bearer-token patterns;
- email addresses;
- MAC addresses;
- RFC1918 private IPv4 addresses;
- CGNAT/Tailscale-style `100.64.0.0/10` addresses;
- Linux/macOS/Windows user home paths;
- configuration keys that request serial numbers, UUIDs, machine/device IDs, MAC, hostname, username, or IP address.

This is a **prefilter**, not a perfect DLP system. It intentionally refuses rather than automatically redacting because automatic redaction can retain dangerous context or alter technical meaning.

## Beginner view

> A community compatibility report should say what hardware/software version was tested, what happened, and how it was tested — without publishing who owns the computer, where it is on the network, or secret account information. Passing the form check means “safe enough to review,” not “this hardware definitely works for everyone.”

## Engineer view

The validator combines Draft 2020-12 JSON Schema validation, recursive high-confidence sensitive-pattern scanning, forbidden-configuration-key checks, and semantic provenance/evidence constraints. It canonicalizes accepted JSON and returns a SHA-256 digest for later evidence linking. It has no hardware probe, uploader, subprocess runner, driver/firmware mutator or auto-fix path.

## Safety and privacy review

- No raw machine dump is accepted by the v0.2 schema.
- No hardware is probed by the validator.
- No file outside the supplied report/schema is inspected.
- No network request or upload is performed.
- No token is redacted and then retained; suspicious submissions are rejected.
- The validator cannot authorize driver, firmware, BIOS or OS changes.
- `safe_to_auto_apply` is schema-enforced `false`.

## Accessibility / multilingual path

The JSON/CLI layer is not the final submission experience. The future Commons UI should render this contract as progressively disclosed Beginner / Intermediate / Engineer forms, explain why identity fields are excluded, support keyboard/screen-reader use, and localize contributor guidance. The structured schema makes those views possible without maintaining separate truth stores.

## What remains before F-04 can be COMPLETE

F-04 remains **IN PROGRESS**. Material unresolved gates include:

- dedicated Commons public distribution/search surface;
- explicit release/version/changelog for the Commons itself;
- safe adapters for reviewed upstream evidence such as hw-probe and fwupd/LVFS reports;
- representative Windows/Linux/macOS submission and reproduction acceptance;
- contributor consent and deletion/correction workflows;
- duplicate/contradiction handling across reports;
- confidence aggregation without turning popularity into truth;
- hardware/version lifecycle and stale-evidence handling;
- accessibility/multilingual human acceptance;
- independent privacy/security review;
- community moderation and abuse/spam controls;
- canonical release and completion evidence.

No production/device mutation is authorized by this tranche.
