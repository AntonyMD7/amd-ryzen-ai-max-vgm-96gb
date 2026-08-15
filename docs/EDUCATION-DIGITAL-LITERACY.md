# Education & Digital Literacy Reference Layer

Status: **IN PROGRESS reference implementation** for `P-109` through `P-118` and `P-120`, while preserving earlier `P-119 Learning-by-Doing Repository Framework` evidence in `learning-git`.

## Search before build

Mature education/content ecosystems already exist. **Moodle** is a broad open-source learning platform; **Jupyter Book** provides a mature path for reproducible, executable technical books/documentation. The portfolio should integrate, contribute or borrow standards from established systems rather than recreate a full LMS or notebook publishing stack without need.

For phishing-awareness training, tools such as **Gophish** demonstrate that full campaign simulation already exists. This public reference deliberately does **not** implement campaign sending, tracking pixels, external deceptive domains or credential capture; it restricts P-117 to local/static educational examples and immediate debriefing.

## Safety and learner privacy

The reference module reads no student records, browsing history, messages, passwords, assessment submissions or private source text. It calls no model, records no grades and changes no account/device.

`P-109` requires authorized-corpus grounding, citations and insufficient-evidence refusal. `P-110` preserves access to the source rather than substituting a summary for it. `P-111` requires visible steps/assumptions/verification rather than an unexplained answer. `P-112` and `P-113` keep assessment/curriculum creation separate from grading/adoption authority.

`P-114` defines beginner/intermediate/expert explanation contracts without assuming the tiers are semantically equivalent until reviewed. `P-115` emphasizes learning-by-doing with safe sandbox/screenshots and recovery. `P-116` teaches source/domain/permission/update/reporting habits without opening URLs or downloading files.

`P-117` is intentionally content-light and defensive: local/static examples only, no sending, credential collection, deceptive domain registration or tracking pixels. `P-118` never asks for a password or password hash; it checks whether password-manager, MFA and reuse-risk concepts are covered.

`P-120` treats mutating executable examples as `NO_EXECUTION`; non-mutating examples still require an ephemeral sandbox, pinned dependencies, expected output, timeout/resource limits, no secrets/network by default and cleanup.

## Accessibility and inclusion

Learning content should expose plain-language and technical paths, keyboard/screen-reader accessible delivery, captions/transcripts for media, readable mathematical notation, reflow/large-text support, and language/local-context review. Assessments should not silently infer ability, disability, intelligence or risk from interaction telemetry.

## Completion gaps

These roadmap items remain IN PROGRESS. Completion requires real user-facing teaching surfaces, licensed/authorized corpora, instructional-design review, factual/domain acceptance, learner privacy/security review, accessibility and multilingual validation, real assessment/executable-doc sandboxing, versioned releases, contribution paths, known limitations and canonical completion records. P-117 additionally requires an explicit ethical/safe training policy and controlled acceptance that proves no credential collection or external deceptive delivery.
