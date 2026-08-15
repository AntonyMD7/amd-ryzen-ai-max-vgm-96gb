# Hardware Compatibility Commons — governed external sources v0.1

**Roadmap:** F-04 Hardware Compatibility Commons  
**Status:** IN PROGRESS  
**Default:** reference external ecosystems; import only narrowly reviewed normalized derived facts

## Search-before-build decision

Hardware Compatibility Commons should not become another crawler that copies mature hardware ecosystems into a second database.

Two upstream ecosystems are especially relevant:

1. **Linux Hardware / hw-probe.** `hw-probe` already collects hardware information, checks operability and contributes reports to the Linux Hardware Database. The companion `linuxhw/HWInfo` repository publishes collected hardware-information reports under **CC BY 4.0**.
2. **fwupd / Linux Vendor Firmware Service (LVFS).** LVFS already provides firmware metadata/distribution infrastructure consumed by fwupd and supports report/metadata workflows.

F-04's distinct value is a privacy-minimized, rights-aware compatibility-evidence contract that can link or adapt external facts without turning someone else's dataset into unreviewed DAIS truth.

## Why raw Linux Hardware reports are not imported

The `hw-probe` project documents privacy protections, including attempts to obscure usernames, hostnames, IP/MAC addresses, UUIDs and serials. Its documentation also makes clear that automatic decoration can fail and that some salted hashed identifiers may be used to identify devices across probes.

That is useful upstream behavior, but it is not equivalent to the stricter F-04 public-data contract. DAIS therefore does **not** accept a raw hw-probe report or probe identifier into the public commons.

The v0.1 adapter accepts only a separately normalized observation after a review has explicitly established:

- the source is the canonical `linuxhw/HWInfo` dataset;
- the relevant dataset license is recorded as `CC-BY-4.0`;
- publication of the particular derived facts has been reviewed;
- unique-device/private identifiers have been removed;
- an exact source snapshot SHA-256 and snapshot reference are retained;
- the normalized record passes the existing F-04 secret/PII/network/user-path prefilter again.

The source URL and declared license remain in the resulting limitations/evidence rather than being erased during normalization.

## Why LVFS is reference-only in v0.1

LVFS is a high-value authoritative ecosystem for firmware metadata and update delivery, but usefulness does not automatically grant DAIS a redistribution/import contract.

The v0.1 schema can represent an `LVFS_PUBLIC_METADATA_REFERENCE`, but the adapter deliberately refuses to convert it into an HCC report. The source must remain:

```text
license_expression = UNRESOLVED_REFERENCE_ONLY
rights_status      = REFERENCE_ONLY
```

until a separate field-level privacy, licensing/redistribution and attribution review establishes exactly what may be imported and how. A caller cannot bypass that policy by self-declaring `CC-BY-4.0` or an approved rights state.

F-04 may still link users to current LVFS/fwupd sources where useful; reference and redistribution are different operations.

## External observation contract

`schemas/hardware-external-observation-v0.1.schema.json` requires:

- named source class;
- canonical HTTPS dataset URL;
- exact source snapshot SHA-256;
- snapshot/commit-like reference;
- explicit license-expression state;
- explicit derived-fact rights state;
- explicit privacy-review state;
- reviewed timestamp;
- normalized hardware/software/configuration fields;
- external observation state and aggregate count.

The adapter performs **no network request**. It cannot fetch, scrape or discover external data. A separate future acquisition process would have to retain and review its own source evidence before invoking this adapter.

## Promotion semantics

External evidence is intentionally weaker than independently reproduced DAIS evidence.

For an approved LinuxHW normalized observation:

```text
COMMUNITY_WORKING   ┐
COMMUNITY_FAILING   ├──> COMMUNITY_REPORTED
COMMUNITY_PARTIAL   ┘
UNKNOWN ----------------> UNKNOWN
```

Nothing from this adapter can become `VERIFIED_WORKING` or `VERIFIED_FAILING`.

A verified HCC status still requires the existing reproducible-test path, at least one actual DAIS reproduction run, artifact evidence and review. This prevents a large external aggregate count from masquerading as DAIS reproduction evidence.

## Privacy and security boundary

The normalized external input is re-scanned by the same F-04 intake privacy detector used for native reports. It rejects, among other things:

- private key/token patterns;
- email addresses;
- MAC addresses;
- RFC1918 and CGNAT IPv4 literals;
- Linux/macOS/Windows user-home paths;
- configuration fields that look like serial, UUID, machine/device ID, MAC, hostname, username or IP identifiers.

Refusal is preferred to automatic lossy redaction. No raw external log is emitted.

## Licensing boundary

Recording `CC-BY-4.0`, a source URL and a snapshot digest is a provenance/rights control, not legal advice. Before a public release that republishes external derived data at scale, attribution presentation, database-right questions where applicable, source terms and downstream distribution obligations should receive appropriate review.

The v0.1 adapter is deliberately narrower than the schema could theoretically permit.

## Acceptance evidence

The repository includes synthetic fixtures only. No real Linux Hardware or LVFS user/device record is copied into source control.

Hosted acceptance requires:

- the reviewed LinuxHW synthetic fixture to become only `COMMUNITY_REPORTED` and pass the existing public intake validator;
- an external failing observation to remain community-reported rather than verified failure;
- rights/privacy/license/canonical-source violations to fail closed;
- sensitive identifiers to be refused;
- the LVFS fixture to return an explicit **blocked/reference-only** result;
- deterministic normalized output;
- absence of network/execution primitives.

## Beginner interpretation

> “We can use information from established hardware communities without pretending it is our own test. Before showing it as evidence, we strip identifying details, keep where it came from and its license, and label it as community-reported. We only call something verified after a reproducible test.”

## Remaining F-04 gates

F-04 remains **IN PROGRESS**. Material completion work still includes:

- governed real external-source acquisition/refresh with source authenticity/freshness evidence;
- explicit LVFS or other dataset rights/field reviews before any import;
- multiple independent real hardware observations;
- moderation, correction/removal, abuse and retention policies;
- richer accessible browse/query UI;
- F-05 signed provenance for imported datasets and public reports;
- versioned distribution/release and community feedback;
- canonical completion evidence.

No compatibility certification or safe-to-auto-apply claim is created by this tranche.
