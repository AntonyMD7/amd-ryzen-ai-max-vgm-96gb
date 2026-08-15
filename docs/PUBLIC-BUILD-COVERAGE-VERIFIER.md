# DAIS Public-Build Coverage Verifier

This verifier provides a machine-checkable answer to one narrow question: **does every canonical `P-001` through `P-227` opportunity have at least one mapped public source/reference evidence tranche, and do all six flagship foundations have mapped public evidence paths?**

It deliberately does **not** answer whether any project is complete.

## Claims it can support

When `scripts/public_build_coverage.py` returns `coverage_gate: PASS`, it supports the statement that:

- exactly 227 canonical opportunity IDs are mapped;
- each is mapped once in the coverage registry;
- all six flagship foundations have evidence mappings;
- the listed local proving-ground evidence paths exist at the tested commit.

## Claims it cannot support

A PASS does not prove:

- a dedicated repository or distribution exists for every project;
- licensing has been resolved for every standalone project;
- README/START-HERE/architecture/recovery documentation is complete for every project;
- security, privacy, accessibility or multilingual acceptance is complete;
- real-world acceptance has occurred;
- a version/tag/release has been published;
- any project is production ready or meets the canonical `[x] COMPLETE` contract.

The emitted report therefore hard-codes `roadmap_complete_count: 0`, `roadmap_completion_proven: false`, `release_proven: false`, and `real_world_acceptance_proven: false` until separate canonical evidence legitimately changes those states.

## Why this matters

Portfolio-scale work can silently lose IDs, duplicate ownership or overstate breadth. The verifier turns the `227/227 source/reference coverage` milestone into an exact-head CI assertion while keeping it semantically separate from project completion.

The mapping is maintained in explicit tranches so future extraction into dedicated repositories can preserve stable canonical IDs and evidence lineage instead of re-numbering projects.
