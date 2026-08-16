# DAIS Issue Template Generator v0.8.0 — Release Notes

Roadmap ID: **P-053**

Release status: **candidate source pending governed publication and released-ref acceptance**.

## What ships

- deterministic GitHub Issue Form bundle generation from a strict bounded JSON specification;
- reusable composite Action at `.github/actions/issue-template-generator`;
- three fixed presets: `bug`, `feature`, and `support`;
- optional sanitized environment field for bug/support reports;
- generated `dais-support.yml` plus chooser `config.yml` only;
- mandatory privacy/scope confirmations in generated forms;
- refusal of unknown keys, invalid types, overlong values, obvious secret-like specification values, path traversal, symlinks, and unsafe output destinations;
- deterministic bundle SHA-256 across exact generated filenames and bytes;
- no network client, GitHub API mutation, issue creation, label/project/assignee lookup, repository commit, or permission mutation;
- hosted deterministic acceptance, adversarial tests, beginner documentation, engineering/threat-model documentation, recovery guidance, and privacy-safe support reporting.

## Upstream authority boundary

GitHub remains the authority for Issue Forms, chooser configuration, repository Issues settings, and actual rendering/validation on the default branch. P-053 does not invent another issue tracker or generic form language; it generates a deliberately narrow documented subset.

## Privacy and safety

Generated forms explicitly instruct reporters not to include credentials, private repository content, personal/medical data, private network details, usernames, hostnames, IP addresses, serial numbers, or private paths where relevant. The generator rejects several obvious secret-like values in its own configuration, but it is not a DLP system and cannot guarantee future reporters comply.

The Action writes generated files only to runner-temporary storage. Copying or committing them into a repository is a separate human/governed action.

## Accessibility and localization boundary

The generator emits text-first GitHub-native Issue Form controls with explicit labels, descriptions, required-state semantics, and language-neutral deterministic machine outputs. GitHub owns final rendered accessibility behavior. v0.8.0 documentation and generated human text are English-first; WCAG conformance, human assistive-technology acceptance, and multilingual user acceptance are not claimed.

## Recovery

The generator is non-mutating. Delete temporary/generated files and rerun from the same specification to reproduce the same bundle digest. If generated files are later committed and prove unsuitable, normal Git revert/PR governance is the recovery path.

## Completion boundary

Publication alone does not make P-053 complete. Completion still requires an exact-source governed `v0.8.0` release, independent released-ref execution against representative public-repository input, retained evidence, fresh 19-gate completion audit, final handover/build record, post-merge verification, and canonical DAIS synchronization.
