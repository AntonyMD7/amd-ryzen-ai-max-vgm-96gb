# Travel, Civic & Public Information — Public Reference Layer

**Roadmap status:** `P-173` through `P-182` are **IN PROGRESS** reference work only.

## Search-before-build

Travel/visa/government/legal information is jurisdiction- and time-sensitive, so authoritative government sources must remain primary. GOV.UK Design System/GOV.UK Frontend demonstrate mature accessible public-service interface patterns and should inform form/plain-language UX rather than being copied blindly across jurisdictions. CKAN is an established open-source data portal platform; Plotly/Dash is an established open-source visualization framework. OpenFisca/PolicyEngine-like systems demonstrate structured legislation/policy modelling, but a model is not the official law.

## Boundaries

- P-173/P-177/P-179 organize document/checklist/deadline **fields**, not passport numbers or other sensitive values in public fixtures; no deadline is verified without a fresh official source.
- P-174 records a dated official visa checklist source; it never determines eligibility or submits an application.
- P-175 creates an accessible itinerary plan; booking/live availability remain separate current-data operations and accessibility details require confirmation.
- P-176/P-178/P-180 create a plain-language transformation plan only. Legal meaning must be preserved and reviewed; the output is not legal advice or an official interpretation.
- P-181/P-182 record open-data source/license/update metadata. Figures and visualizations must retain provenance and cannot be treated as verified merely because parsing succeeds.

## Completion gaps

No mapped item is COMPLETE. Required future gates include dedicated public interfaces, explicit licenses, jurisdiction/source freshness logic, privacy threat modelling, accessibility/multilingual acceptance, official-source reconciliation, real-world user testing, versioned releases and canonical completion evidence.
