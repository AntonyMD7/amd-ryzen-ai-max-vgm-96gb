# Beginner Tech Rescue — Public Reference v0.1

Roadmap mapping:

- `P-001 Beginner Tech Rescue Toolkit` — **IN PROGRESS**
- `P-017 Error Message Plain-English Translator` — **IN PROGRESS**
- `P-018 Safe Command Explainer` — **IN PROGRESS**
- `P-020 Verified Technical Runbook Generator` — **NOT YET IMPLEMENTED**; the rescue outputs can become inputs to a future evidence-backed runbook layer.

The reference implementation is deliberately **explain-first and non-mutating**. It has no `repair` or `execute` subcommand.

## Search-before-build

Useful existing ecosystems already cover command education and specialist analysis. The TLDR-pages ecosystem provides concise community command examples; tools such as ShellCheck analyze shell scripts; ExplainShell-style tools demonstrate shell-command decomposition. Future work should integrate or link to authoritative/upstream command documentation rather than trying to maintain a complete command encyclopedia here.

The gap this project explores is a beginner safety contract:

```text
WHAT HAPPENED?
     ↓
WHAT DOES IT PROBABLY MEAN?
     ↓
WHAT CAN I CHECK WITHOUT CHANGING ANYTHING?
     ↓
WHAT COMMAND AM I ABOUT TO RUN?
     ↓
WHAT COULD THAT COMMAND CHANGE?
     ↓
ONLY THEN: governed repair planning
```

## One safe entry point

`scripts/beginner_tech_rescue.py` exposes only:

- `health` — calls the read-only System Doctor baseline;
- `error` — explains a known error category and read-only next checks;
- `command` — explains/classifies command text without running it.

No repair path is present in v0.1.

## Error explainer

`scripts/error_message_explainer.py` uses a small deterministic catalog for common categories such as:

- command not found;
- permission/access refused;
- connection refused;
- DNS resolution failure;
- storage full;
- Git merge conflict;
- authentication failure;
- timeout.

Every match is phrased as a possible category, not a proven root cause. Unknown messages fail honestly to `UNKNOWN` and direct the user toward preserved sanitized evidence and authoritative documentation.

Secret-like token/password/API-key fragments are redacted before the input is returned in structured output.

## Safe Command Explainer

`scripts/safe_command_explainer.py` statically reviews command text and never executes it.

The catalog distinguishes lower-risk read-only commands from context-dependent, network, privileged, mutating, disruptive and code-executing commands. It also recognizes high-risk patterns such as:

- recursive forced deletion;
- `git reset --hard`;
- forced Git cleaning;
- force push;
- download-and-immediately-execute pipelines;
- world-writable permission changes;
- weakened PowerShell execution policy.

A lower-risk classification is explicitly named `LOWER_RISK_NOT_GUARANTEED_SAFE`. Static analysis cannot know aliases, expansion, filesystem targets, permissions, remote endpoints or what an invoked program actually does.

Commands containing token/password/secret/API-key assignments are not echoed back into output.

## Beginner example

```text
$ python scripts/beginner_tech_rescue.py command "git reset --hard HEAD~1"
Runs Git subcommand 'reset'.
Classification: HIGH_RISK_REVIEW
Review: hard Git reset can discard worktree/index changes
Do not run this command until each risk reason and target is understood.
The command was not executed.
```

The point is not to frighten the user. It is to insert an understandable inspection boundary before a potentially irreversible action.

## Security and privacy

- no command execution;
- no automated repair;
- no remote requests;
- no user-document reading;
- secret-like command fragments are redacted;
- error input is truncated in structured output;
- no root-cause claim from pattern matching;
- command classes are educational heuristics, not a security verdict.

## Accessibility and language

The current CLI uses short plain-language sentences and structured JSON that can feed the Accessible AI renderer. This is not sufficient for completion: a dedicated UI, keyboard/screen-reader acceptance, large-text/reflow validation and broader multilingual output remain required.

## Completion gaps

None of the mapped items is COMPLETE. Remaining work includes dedicated public distribution, explicit licensing for the generic package, a broader reviewed error/command corpus, authoritative documentation links, Windows/PowerShell-specific parsing, shell-aware parsing beyond simple static heuristics, evidence/runbook export, accessibility/multilingual acceptance, real-world beginner testing, versioned release and canonical completion evidence.
