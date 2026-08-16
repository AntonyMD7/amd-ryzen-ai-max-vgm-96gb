# P-058 Dangerous-Script Detector v0.12.0 — Final Completion Record

**Roadmap ID:** P-058  
**Product:** DAIS Dangerous-Script Detector  
**Release:** v0.12.0  
**Released source:** `5ba437c2d39e60d59df43fe356b3727ea3ba319a`  
**Completion candidate date:** 2026-08-16

## Product outcome

P-058 is a bounded, non-executing public GitHub Action and standard-library Python detector for surfacing a deliberately small set of high-risk script constructs before repository scripts are trusted or run. It emits deterministic privacy-minimized evidence and deliberately refuses to treat either a finding or a clean scan as proof of intent or safety.

The product is complete only within that declared scope. It is not a malware classifier, sandbox, full static-analysis engine, AST/data-flow analyzer, or replacement for specialist tools and human security review.

## Search-before-build decision

The product preserves established specialist ecosystems rather than replacing them. ShellCheck remains a specialist shell analyzer; GitHub CodeQL remains a mature GitHub/application-code analysis ecosystem; Semgrep remains a broader pattern-based SAST ecosystem. P-058 contributes a small portable DAIS policy/evidence layer with strict non-execution, containment, privacy and fail-honest semantics.

## Architecture and safety boundary

The released product:

- discovers only the supported bounded script/workflow file classes;
- rejects unsafe roots, traversal, symlinked candidates, binary/NUL content and non-UTF-8 input;
- enforces file-count, per-file and aggregate byte limits;
- applies only the fixed reviewed v0.12.0 rule set;
- records rule/severity/category/language/line number plus cryptographic fingerprints rather than raw source or paths;
- contains no repository-supplied rule/plugin facility;
- performs no subprocess execution, network request, repository-code execution or repository mutation;
- fails the Action for HIGH/CRITICAL findings while preserving MEDIUM as explicit review evidence;
- keeps all safety/repository-security claims hard false.

Recovery is discard-and-rerun because scanned content is never mutated. A consumer can roll back the integration by pinning a prior reviewed ref or removing the Action invocation.

## Recursive red-team defect and permanent fix

After the first source productization merged, recursive review found a meaningful false-negative shape: workflow YAML identification was relative only to the caller-selected scan root. A consumer narrowing `root` to `.github/workflows` could therefore cause those same workflow files to lose their repository workflow identity and be skipped.

The stale-base implementation PR was deliberately not merged. The fix was rebuilt on current canonical main, changed classification to use the resolved repository workspace, retained the selected scan root only for containment/privacy-relative evidence, and added `test_workflow_directory_subroot_is_still_scanned`. Exact-head Safety and P-058 acceptance passed before merge.

Fresh exact-main P-058 acceptance on corrected source `5ba437c2d39e60d59df43fe356b3727ea3ba319a` passed as run **31947900033**, retaining artifact **9263811361**, SHA-256 `ac7c01968c1a299dd0a3f5cc50e14689df241f43c752fd0891f25e1626ef66a4`.

## Governed release

Release-control PR #135 originally exposed two orchestration defects and both were fixed without weakening product gates:

1. the release workflow attempted to use pytest without installing it; because the P-058 test module is deliberately executable directly, the permanent fix removed that unnecessary dependency rather than adding network/package installation;
2. the first P-058 manifest contained keys outside the already-governed release schema; it was corrected to the exact existing schema rather than weakening the manifest validator.

The corrected release-control exact head passed its dedicated release validation and Safety checks, then merged to canonical public main at `c4b6b848f676199a7f3d48fa0d28366549aadf3d`.

Push run **31948147029** then:

- revalidated exact retained release source;
- re-ran all 12 adversarial tests;
- reverified exact source-acceptance run/artifact identity;
- passed non-mutating governed release planning;
- published public non-draft/non-prerelease `v0.12.0`;
- independently verified the public tag resolves exactly to `5ba437c2d39e60d59df43fe356b3727ea3ba319a`;
- consumed the released Action against pinned real public `AntonyMD7/learning-git` commit `01723a1825113de08810193f37e8047d978433c2` with zero consumer mutation;
- separately re-exercised the workflow-subroot regression on the **released ref** and required the expected fail-closed high-risk detection;
- verified sanitized evidence does not retain the fixture source line or file path.

Retained release evidence:

- release-plan artifact **9263877147**, SHA-256 `947657f6110bb5a936abdb57d4c5f915d45de490561e980640fcf39510f58d3c`;
- publication artifact **9263880389**, SHA-256 `347e08cf9488dd13f0a5c0ccd2f1def490de0b3f15d451d8a0df19edd1c40120`;
- released-ref artifact **9263882099**, SHA-256 `448fd183e84d75c0ac6574787a851586681dfb66b12a573f12f0ca8cf940b20f`.

The release was published at 2026-08-16T12:50:54Z.

## Accessibility and multilingual review

P-058 is text-first JSON/Markdown with explicit labels, stable machine-readable states and no color-only/pointer-only interaction. That supports accessible integration, but it is not a WCAG or human assistive-technology certification.

Rule IDs, status/severity values and evidence keys are language-neutral integration surfaces. Human documentation is English-first. Professional translation and human multilingual usability acceptance are not claimed.

## Privacy review

Evidence intentionally omits raw source lines, matched text and absolute/relative plaintext file paths. Publicly retained evidence is sanitized. The product does not retain credential values or private-infrastructure content by design. Dedicated support reporting also directs contributors away from posting sensitive script contents.

## Known limitations

A clean P-058 scan proves only that the exact reviewed rule set found no matching construct in the exact scanned inputs. P-058 does not establish script safety, repository security, developer intent, complete behavior coverage, deobfuscation, binary safety, future-version safety or the correctness of specialist analyzers. New language/rule coverage requires the same review/test/evidence process rather than silent expansion.

## Completion contract

`examples/public-build-completion-p058-v0.12.0.json` records all 19 canonical gates as PASS with applicability reviewed. Final completion still requires the dedicated exact-head completion workflow to independently re-audit the record, public release/tag, source/release evidence identities and a fresh released-ref public-consumer run. Only after that workflow passes, the completion PR merges, fresh post-merge completion verification passes, and canonical private DAIS status is synchronized may P-058 be treated as canonically COMPLETE.

No flagship or adjacent product is promoted by implication.
