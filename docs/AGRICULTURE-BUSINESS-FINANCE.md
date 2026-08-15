# Agriculture, Business & Finance — Public Reference Layer

**Roadmap status:** `P-156` through `P-172` are **IN PROGRESS** reference work only.

## Search-before-build

The public layer should compose established systems rather than create another ERP/accounting platform. **farmOS** is an existing web application for farm management, planning and record keeping. **Odoo** already spans CRM, inventory, billing/accounting and related business functions. **Firefly III** is an established open-source personal-finance manager. Accounting/invoice products such as Akaunting and Invoice Ninja exist, but exact edition/license terms must be reviewed before reuse or redistribution; availability of source on GitHub is not by itself a license conclusion.

This tranche therefore implements only transparent arithmetic, manifests and comparison contracts.

## Scope

- P-156/P-160: farm record manifest; no sensor/device write.
- P-157/P-158: user-supplied poultry/feed arithmetic; no husbandry recommendation.
- P-159: area/depth-to-volume arithmetic; no irrigation schedule/agronomic claim.
- P-161/P-172: inventory count reconciliation; no stock/accounting mutation.
- P-162: quote arithmetic only; no invoice issuance or tax-compliance claim.
- P-163: customer follow-up plan only; no customer-data collection or message sending.
- P-164/P-165: business/break-even arithmetic only; not a viability/investment conclusion.
- P-166/P-167: budget/debt arithmetic education; no credit/investment advice.
- P-168/P-169/P-170: provider eligibility/fee comparison structure; live terms are explicitly unverified and no account/payment action occurs.
- P-171: procurement cost comparison; no supplier selection/order.

## Safety, privacy and evidence

Financial/payment eligibility, fees, taxes and provider availability are time- and jurisdiction-sensitive. A production comparator must fetch current primary-provider terms with a retrieval timestamp and must distinguish published eligibility from actual account approval. Tax/accounting/legal claims require jurisdiction-specific professional review. Personal/customer/payment credentials are outside the public fixture contract.

Agricultural calculators expose assumptions and units; arithmetic output is not veterinary, agronomic or food-safety advice. Hardware/sensor actuation would require a separate SafeFix-governed mutation path.

## Completion gaps

No mapped item is COMPLETE. Dedicated applications, explicit project licenses, source/version provenance, accessibility/multilingual testing, representative real-world acceptance, jurisdiction/provider refresh logic, security/privacy review, releases and canonical completion records remain required.
