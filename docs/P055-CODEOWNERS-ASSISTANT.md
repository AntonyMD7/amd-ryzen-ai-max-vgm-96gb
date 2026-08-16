# P-055 CODEOWNERS Assistant — Engineering, Threat and Evidence Model

Roadmap ID: **P-055**  
Candidate version: **0.10.0**  
State: **IN PROGRESS**

## Product decision

Fresh search-before-build reviewed GitHub's current CODEOWNERS and protected-branch documentation. GitHub remains the platform authority: it selects CODEOWNERS from `.github/`, repository root, then `docs/`; evaluates rules from the pull request base branch; supports most but not all gitignore-style pattern features; requires referenced users/teams to have appropriate repository access; can report CODEOWNERS errors server-side; and can enforce code-owner review through branch protection/rulesets.

P-055 therefore **does not implement a competing GitHub authorization or review engine**. It is a bounded local preflight/explanation layer that makes common structural and security mistakes visible before maintainers rely on the file.

## Architecture

```text
trusted P-055 source
      |
      v
explicit repository root
      |
      +--> containment / symlink / regular-file / 1 MiB guards
      |
      +--> GitHub-documented location precedence
      |      .github/CODEOWNERS
      |      CODEOWNERS
      |      docs/CODEOWNERS
      |
      +--> conservative local parser
      |      unsupported negation
      |      unsupported character ranges
      |      unsupported escaped-leading-#
      |      missing/lexically malformed owner token
      |      duplicate exact patterns / order warning
      |      conservative self-protection evidence
      |
      +--> privacy-minimized deterministic report
      |      line numbers + finding classes
      |      owner type/count only
      |      pattern SHA-256, not raw pattern
      |
      +--> EN / ES plain-language guide
```

The composite Action writes only to `RUNNER_TEMP` and may append the guide to `GITHUB_STEP_SUMMARY`.

## GitHub authority boundary

The local parser intentionally has hard-false claims for:

- GitHub server-side syntax verification;
- user/team identity or write-access verification;
- branch-protection/ruleset verification;
- required code-owner review enforcement;
- comprehensive repository ownership coverage;
- repository security.

Those require GitHub's live repository state and, where applicable, the server-side CODEOWNERS errors endpoint or repository settings. A local `CODEOWNERS_LOCAL_BASELINE_READY` status therefore remains a preflight result, not a platform certification.

## Documented syntax checks

The assistant flags forms GitHub documents as unsupported in CODEOWNERS:

- `!` negation;
- `[]` character-range syntax;
- escaping a leading `#` with `\`.

It also requires at least one locally recognizable owner token per rule. Owner tokens may be `@user`, `@org/team`, or an email-shaped token. Lexical recognition is **not** proof that the user/team/email maps to an eligible GitHub account with write access.

## Rule order and precedence

The product reports:

- lower-priority local CODEOWNERS files when a higher-priority file is effective;
- duplicate **exact** patterns, because later matching rules matter.

It deliberately does not claim a complete reimplementation of GitHub's glob matching. That avoids a dangerous false assurance where a local matcher disagrees with GitHub.

## CODEOWNERS self-protection

GitHub recommends assigning an owner to CODEOWNERS itself or its containing `.github` directory when code-owner review is part of repository protection. P-055 detects only a conservative explicit subset (`CODEOWNERS`, the containing directory, or broad all-file patterns). A negative result is phrased `SELF_PROTECTION_NOT_PROVEN`, not `UNPROTECTED`, because GitHub's full pattern semantics remain authoritative.

## Threat model

### Assets

- repository source and ownership policy;
- owner identities/team structure;
- workflow tokens and runner state;
- private repository path names;
- branch/ruleset security posture.

### Untrusted inputs

- audited repository root;
- CODEOWNERS bytes and paths;
- caller language/output parameters.

### Controls

- no GitHub API or other network client;
- no credential/token input;
- no subprocess or repository-code execution;
- no repository mutation or review request;
- candidate symlinks fail closed;
- file size is bounded to 1 MiB;
- output must live outside the audited repository;
- reports retain no raw owner token;
- rule patterns are SHA-256 fingerprinted rather than copied;
- absolute local filesystem paths are absent from the report;
- English/Spanish guide wording is product-owned fixed text.

## Accessibility and multilingual design

The product is text-first. JSON is machine-readable and Markdown has headings/lists with no color-only meaning. English and Spanish guides are presentation layers over one deterministic evidence object; changing language does not change technical status. This is an accessibility review and multilingual path, not WCAG conformance, assistive-technology user acceptance, or professional translation certification.

## Recovery

P-055 is read-only. Recovery is deletion of external/runner-temporary outputs followed by a rerun. Any maintainer edit to CODEOWNERS is outside this tool and remains recoverable through normal Git history/revert.

## Acceptance strategy

Source acceptance requires:

1. adversarial unit tests for precedence, unsupported syntax, owner privacy, duplicate-order warnings, self-protection semantics, symlink/size/output-containment refusal, deterministic EN/ES evidence, and no network/subprocess authority;
2. valid and invalid disposable fixtures on GitHub-hosted Ubuntu;
3. read-only audit of a pinned real public repository checkout;
4. repeated evidence digest identity;
5. consumer README and Git tree immutability;
6. sanitized artifact retention;
7. no completion promotion.

## Release and completion boundary

Source/CI success is not completion. P-055 still requires an exact-source versioned release, released-ref real-public acceptance, retained release evidence, a full 19-gate completion record, final handover, fresh post-merge verification and canonical DAIS status synchronization.

## Known limitations

- no GitHub server-side error retrieval in v0.10.0;
- no user/team existence or write-access verification;
- no full GitHub glob evaluator;
- no changed-file ownership simulation;
- no branch protection/ruleset inspection;
- no automatic CODEOWNERS write/fix;
- no review-request mutation;
- no guarantee that ownership policy is organizationally correct or sufficient.
