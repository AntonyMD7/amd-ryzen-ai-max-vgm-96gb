# Health, Medicine & Emergency Support — Public Reference Layer

**Roadmap status:** `P-134` through `P-147` are **IN PROGRESS** reference work only.

This tranche establishes conservative data/provenance contracts for public medical education, equipment/inventory organization, evidence navigation, emergency preparedness and future clinical-tool integration. It is **not** a diagnostic, prescribing, treatment, interaction-checking, clinical-calculator, emergency-dispatch or patient-record system.

## Search-before-build / adoption boundary

The design intentionally wraps or interoperates with established authoritative ecosystems instead of inventing parallel medical vocabularies or evidence databases:

- **NLM RxNorm** is the preferred medication identity vocabulary/API layer for normalized drug identifiers.
- **NLM DailyMed / FDA Structured Product Labels** are preferred public label-information sources; source/version provenance must be retained.
- **NCBI Entrez E-utilities / PubMed / PMC** remain the literature-retrieval authority for evidence-navigation integrations. Retrieval is not evidence appraisal.
- **HL7 FHIR** is the interoperability target for future structured health-data exchange where a deployment is legally and clinically appropriate. This public reference layer does not publish or ingest real patient records.
- **FEMA Ready.gov and local emergency authorities** are general preparedness sources. Local emergency, clinical, offshore, workplace and jurisdiction-specific protocols supersede generic content.
- Anatomy datasets, translations, formularies, clinical scores and offline reference packages must be reviewed separately for license, representation, clinical currency and redistribution rights.

## Mapped roadmap capabilities

| ID | Public reference contract | Current scope |
|---|---|---|
| P-134 | Plain-language anatomy/education manifest | Source/version/rights-aware education only; no diagnostic use |
| P-135 | Medication mechanism explainer manifest | RxCUI identity + authoritative sources; no dose/advice/interaction clearance |
| P-136 | Guardrailed clinical calculator manifest | Formula execution disabled; requires independently sourced reference vectors and review |
| P-137 | Clinician evidence-navigation plan | PubMed/PMC retrieval plan only; no ranking or evidence-quality claim |
| P-138 | Remote medical equipment checklist | Inventory/checklist metadata only; no certification claim |
| P-139 | Medical inventory snapshot | Item/count/unit/month-level expiry only; no patient data or procurement action |
| P-140 | Remote medical handover template | Public structure only; real patient data must remain in an approved private clinical system |
| P-141 | Emergency workflow manifest | Protocol ID/version/jurisdiction/source only; no embedded clinical execution |
| P-142 | Public-health information manifest | Provenance/language metadata; no copied source body or medical advice |
| P-143 | Health-literacy transformation plan | Preserve numbers/units/warnings; clinical-meaning review required |
| P-144 | Medication-list manifest | Minimal medication identity only; no patient identifier or implicit cloud upload |
| P-145 | Medication-interaction information plan | Identity/source handoff only; never declares a combination safe or unsafe |
| P-146 | Offline medical reference manifest | Source/version/hash/rights gate; publication fails closed without confirmed rights |
| P-147 | Emergency preparedness checklist | General preparedness categories only; no inferred local emergency numbers or treatment steps |

## Safety and privacy contract

1. **No diagnosis, treatment, prescribing or dose recommendation.** Public code must not present itself as a clinician or emergency service.
2. **No interaction clearance.** A future interaction interface must use current authoritative information and patient-specific clinician/pharmacist review; absence of a detected interaction is not a safety certificate.
3. **Clinical calculators fail closed.** A calculator cannot become clinical-use capable merely because a formula is coded. It requires an exact authoritative source, version, independently sourced reference vectors, implementation review and real acceptance testing appropriate to the intended use.
4. **No PHI in public evidence.** Public fixtures/examples must use synthetic/public information. Patient identifiers, contact details, free-text case narratives and clinical records do not belong in this repository.
5. **No hidden cloud fallback for sensitive data.** Local-sensitive manifests explicitly do not authorize upload.
6. **Emergency workflows are jurisdiction/version bound.** The repository may describe a protocol contract but does not embed or execute a local clinical protocol until the exact version is approved by the responsible clinical authority.
7. **Offline references require provenance, hash, rights and currency review.** A downloadable file is not automatically lawful to redistribute or clinically current.
8. **Anatomy and educational datasets are not universal truth.** Source population, incompleteness, asset licensing and intended use must be surfaced.
9. **Accessibility transformations preserve clinical meaning.** Numbers, units, warnings, contraindication language and uncertainty must not be silently simplified away.
10. **No source-built = clinically validated claim.** CI proves software contract behavior only.

## Beginner experience

A beginner-facing application built on these contracts should say what it can and cannot do in plain language. Typical safe wording is: “I can organize the information, show the source and explain what it means. I cannot decide your diagnosis, dose, treatment or whether a medication combination is safe.”

When emergency content is presented, the interface must direct the user to the applicable local emergency/clinical authority rather than guessing jurisdiction-specific contacts from repository code.

## Engineer experience

An engineer should be able to inspect:

- exact source name, URL, version/access date and stable identifier;
- whether the operation is education, retrieval planning, checklist organization or a future clinical integration;
- whether patient/sensitive data is permitted and whether cloud transfer is authorized;
- formula/protocol version gates and reference-vector requirements;
- rights/hash/currency fields for offline packages;
- explicit `*_performed: false`, `*_enabled: false` and no-overclaim markers;
- test evidence for rejection of patient-like fields, credential-bearing URLs and unsupported identifiers.

## Interoperability direction

Future production-grade implementations should prefer structured identifiers and interoperable resources over proprietary free text. FHIR/RxNorm/SPDX-like provenance references may be linked from DAIS Universal Evidence records, while retaining separate trust semantics: schema validity does not prove clinical accuracy, provenance does not prove suitability, and a public source does not automatically confer redistribution rights.

## Completion gaps

None of `P-134` through `P-147` is COMPLETE. Completion requires, as applicable:

- dedicated public distribution surfaces rather than proving-ground-only modules;
- explicit license and data/content-rights review for each distributed dataset/reference;
- clinical governance and regulatory classification for anything that could influence patient care;
- exact current upstream API integrations with pinned/reproducible evidence;
- accessibility and multilingual evaluation with meaning-preservation acceptance;
- synthetic fixture suites plus independent real-world acceptance in the intended setting;
- security/privacy threat models and PHI/data-retention controls;
- offline failure-mode and clinical-currency tests where offline use is claimed;
- tagged/versioned release, retained evidence and canonical completion record.

Until those gates are satisfied, these modules remain **reference architecture and safety-contract evidence**, not clinical products.
