# Community, Ministry & Nonprofit — Public Reference Layer

**Roadmap status:** `P-148` through `P-155` are **IN PROGRESS** reference work only.

This tranche adds portable, privacy-minimizing contracts around scheduling, events, donation administration, multilingual resources, Scripture study and teaching corpora. It does not replace mature scheduling/CRM/event/Bible-study systems and does not publish private ministry, donor or copyrighted corpus data.

## Search-before-build decisions

- **P-148 Volunteer Scheduling:** prefer integration with established scheduling/constituent systems such as Cal.diy or CiviCRM when their deployment/license/privacy model fits. The reference code plans roles/slots only; it does not assign people.
- **P-149 Community Event Toolkit:** established open-source event platforms such as pretix already handle registration/ticketing. This tranche keeps event metadata separate from registration/payment processing.
- **P-150 Donation Administration:** CiviCRM is an established nonprofit CRM/fundraising ecosystem. This tranche does not build a payment processor, collect card data, make tax-receipt claims or infer accounting compliance.
- **P-151 Multilingual Resource Library:** build around explicit language/source/rights metadata; do not scrape or redistribute material merely because it is publicly reachable.
- **P-152/P-153 Scripture Search and Bible Study:** CrossWire SWORD is an established cross-platform Bible software engine/API. Bible text/modules have their own rights; engine licensing does not automatically license every text.
- **P-155 Historical/Biblical Language Study:** STEPBible publishes reusable data including lexical resources under stated licensing. Preserve attribution, dataset version and field provenance rather than silently copying content into an opaque corpus.
- **P-154 Sermon/Teaching Corpus:** owner/private teaching material must remain private unless explicit publication rights exist. Public examples should use synthetic/public documents and hashes, not private sermon text.

## Privacy and safety boundaries

1. Public repository examples contain no volunteer names, donor identities, addresses, phone numbers, emails, private prayer/ministry records or payment credentials.
2. Scheduling code is plan-only: no person is assigned, messaged or added to a calendar.
3. Event metadata is not a registration/ticketing/payment implementation.
4. Donation administration is not payment processing, accounting, charity-law advice or tax-receipt certification.
5. Multilingual/community content requires source and rights metadata. Public availability is not redistribution permission.
6. Scripture/text licenses are evaluated per module/dataset/content source. The software engine's license cannot be projected onto independently copyrighted translations.
7. Bible-study tooling must distinguish retrieval/source evidence from interpretation. It does not claim theological authority or doctrinal correctness.
8. Historical-language data must retain provenance and should expose textual/data limitations rather than imply that lexical output settles interpretation.
9. Private sermon corpora are never uploaded to a public proving-ground repository merely to demonstrate indexing.

## Beginner experience

A beginner-facing system should make boundaries obvious: “Plan volunteer roles,” “Create an event outline,” “Organize donation categories,” “Search sources I am allowed to use,” or “Study from licensed Scripture/language data.” Actions involving real people, money, messages, registrations or publication require a separate authenticated application and explicit approval.

## Engineer experience

The reference functions expose stable IDs, rights/source URLs, language tags, hashes and no-side-effect markers. Integrations should later prove:

- exact upstream version/commit/API;
- least-privilege permissions;
- retention/deletion policy for personal data;
- time-zone and concurrency behavior for scheduling;
- payment/accounting separation;
- translation and accessibility acceptance;
- module/dataset licensing and attribution;
- synthetic fixture use in public CI.

## Completion gaps

No mapped item is COMPLETE. Completion requires dedicated distribution, explicit project/content licensing, real-world acceptance with representative users, privacy/security review for personal/donor data, accessibility/multilingual testing, exact upstream integrations, offline/low-bandwidth handling where claimed, versioned release and canonical completion evidence.
