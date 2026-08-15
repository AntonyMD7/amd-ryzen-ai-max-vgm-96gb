# Hardware Compatibility Commons Query Layer v0.1

Status: **F-04 IN PROGRESS — read-only public evidence browsing, not compatibility certification**

The Hardware Compatibility Commons already has a privacy-safe intake validator and a conflict-preserving exact-context index. This tranche adds the missing beginning of a **search/browse experience** without weakening those evidence rules.

## Search-before-build

DAIS should not recreate mature hardware ecosystems simply to own a database.

The Linux Hardware Project's `hw-probe` already probes hardware, checks operability and contributes reports to the Linux hardware database. Related Linux Hardware repositories publish collected subsystem reports. `fwupd`/LVFS already owns important firmware metadata, update and reporting workflows.

Hardware Compatibility Commons therefore focuses on a different reusable contract:

```text
sanitized report
      ↓
strict public intake
      ↓
exact hardware/software/configuration context
      ↓
conflict-preserving evidence index
      ↓
read-only query
      ↓
visible evidence state + limitations
```

Future integrations should adapt or link established specialist datasets where licensing, privacy, provenance and API contracts permit rather than silently copying them.

## Query behavior

`scripts/hardware_compatibility_query.py` consumes an already-built schema `0.3` public evidence index and supports composable filters for:

- hardware vendor/model/architecture/accelerator;
- OS and OS version;
- driver and firmware strings;
- configuration key/value;
- aggregate evidence state.

Text filters are case-insensitive substring matches for discoverability. Configuration key/value filters must match within the same configuration item.

The query never reads raw logs or a device and never contacts the network.

## Synthetic evidence is hidden by default

Synthetic conformance fixtures are useful for tests but are dangerous if they look like community compatibility evidence in a normal browse result.

Therefore entries with `real_observation_count == 0` are excluded unless the caller explicitly selects `--include-synthetic`.

Even when shown, their aggregate state remains:

```text
SYNTHETIC_ONLY_NOT_REAL_HARDWARE_EVIDENCE
```

## Conflicts remain first-class

If an exact context has both verified-working and verified-failing observations, the index state remains:

```text
CONFLICT_REQUIRES_REVIEW
```

The query returns that context and both status counts. It does not sort the conflict away, select the majority as truth, or calculate a “compatibility percentage” that would hide contradictory evidence.

## No-match semantics

No matching context means only that the current sanitized index has no matching evidence under the chosen filters.

The response status is deliberately:

```text
NO_MATCH_NO_COMPATIBILITY_INFERENCE
```

It does **not** mean hardware is incompatible.

## Hard-false claims

Every result keeps:

```text
compatibility_certified = false
safe_to_auto_apply = false
conflicts_auto_resolved = false
absence_of_match_means_incompatible = false
majority_vote_used_as_truth = false
external_lookup_performed = false
```

## Example

First build an index using only public-intake-eligible reports:

```bash
python scripts/hardware_compatibility_index.py report-a.json report-b.json > /tmp/hcc-index.json
```

Then query it:

```bash
python scripts/hardware_compatibility_query.py /tmp/hcc-index.json \
  --vendor AMD \
  --os Windows \
  --configuration-key vgm
```

Review returned evidence states and report digests rather than treating a match as permission to apply a fix.

## Privacy and security

The query layer intentionally works only after the existing public-intake boundary. It does not add a bypass around secret/PII/private-network/unique-device-identifier removal.

A production commons would still need abuse controls, moderation, retention policy, provenance, rate limits, dataset licensing analysis and a way to correct/remove unsafe submissions.

## F-04 progression

F-04 now has public reference layers for:

- hardware compatibility report schemas;
- privacy-safe public intake;
- exact-context conflict-preserving indexing;
- read-only search/browse filtering with synthetic-evidence opt-in and no-match truth boundaries.

F-04 remains **IN PROGRESS**. A dedicated commons/database, governed community ingestion/moderation, independent real reports, richer accessible browse UX, external dataset adapters, release/versioning and the rest of the canonical completion contract remain outstanding.
