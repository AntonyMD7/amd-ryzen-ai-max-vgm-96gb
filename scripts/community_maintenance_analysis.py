#!/usr/bin/env python3
"""Transparent, non-mutating public-repository maintenance analysis.

Roadmap scope: P-053, P-062, P-063. All modes consume explicit sanitized JSON;
they do not query GitHub, read local git history, close issues, label users, or
infer contributor identity beyond caller-supplied public labels.
"""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{1,}")
STOP = {
    "the", "and", "for", "with", "this", "that", "from", "into", "when", "then",
    "but", "not", "are", "was", "were", "has", "have", "had", "can", "could",
    "would", "should", "will", "your", "you", "our", "their", "they", "its",
    "issue", "problem", "please", "help", "error",
}


class InputError(ValueError):
    pass


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_label(value: Any, name: str, max_len: int = 240) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise InputError(f"{name} is required")
    return text[:max_len]


def history_explain(data: dict[str, Any]) -> dict[str, Any]:
    commits = data.get("commits") if isinstance(data, dict) else None
    if not isinstance(commits, list) or not commits:
        raise InputError("commits must be a non-empty array")
    if len(commits) > 200:
        raise InputError("at most 200 commits per visualization")

    rows = []
    seen = set()
    for i, item in enumerate(commits):
        if not isinstance(item, dict):
            raise InputError(f"commit {i} must be an object")
        sha = str(item.get("sha", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{7,40}", sha) or sha in seen:
            raise InputError("commit sha must be unique 7-40 hex characters")
        seen.add(sha)
        message = clean_label(item.get("message"), f"commit {sha} message", 160)
        parents = item.get("parents", [])
        if not isinstance(parents, list) or any(not isinstance(p, str) for p in parents):
            raise InputError(f"commit {sha} parents must be an array of sha strings")
        rows.append({"sha": sha, "short": sha[:8], "message": message, "parents": [p.lower() for p in parents]})

    index = {x["sha"]: x for x in rows}
    edges = []
    for row in rows:
        for parent in row["parents"]:
            exact = index.get(parent)
            if exact is None:
                matches = [x for x in rows if x["sha"].startswith(parent) or parent.startswith(x["sha"])]
                exact = matches[0] if len(matches) == 1 else None
            if exact:
                edges.append((exact["sha"], row["sha"]))

    lines = ["flowchart LR"]
    for i, row in enumerate(rows):
        label = html.escape(f"{row['short']} {row['message']}", quote=True).replace('"', "&quot;")
        lines.append(f'  c{i}["{label}"]')
    idx = {row["sha"]: i for i, row in enumerate(rows)}
    for parent, child in edges:
        lines.append(f"  c{idx[parent]} --> c{idx[child]}")

    roots = [x["short"] for x in rows if not any(child == x["sha"] for _, child in edges)]
    tips = [x["short"] for x in rows if not any(parent == x["sha"] for parent, _ in edges)]
    merge_commits = [x["short"] for x in rows if len(x["parents"]) > 1]
    return {
        "schema_version": "0.1",
        "mode": "VISUAL_GIT_HISTORY_EXPLAINER",
        "mermaid": "\n".join(lines) + "\n",
        "summary": {"commit_count": len(rows), "known_edge_count": len(edges), "roots_in_input": roots, "tips_in_input": tips, "merge_commits": merge_commits},
        "limitations": [
            "Only caller-supplied commits are shown; missing parents/history can make roots or tips incomplete.",
            "Graph topology does not explain why a change was correct, safe, or reviewed.",
            "Author identity is intentionally not required for visualization.",
        ],
        "execution": {"git_history_queried": False, "repository_changed": False, "network_request_performed": False},
    }


def contributor_absence(data: dict[str, Any]) -> dict[str, Any]:
    contributors = data.get("contributors") if isinstance(data, dict) else None
    if not isinstance(contributors, list) or not contributors:
        raise InputError("contributors must be a non-empty array")
    normalized = []
    for i, item in enumerate(contributors):
        if not isinstance(item, dict):
            raise InputError(f"contributor {i} must be an object")
        label = clean_label(item.get("label"), f"contributor {i} label", 120)
        count = item.get("contributions")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise InputError("contributions must be non-negative integers")
        normalized.append({"label": label, "contributions": count})
    total = sum(x["contributions"] for x in normalized)
    if total <= 0:
        raise InputError("total contributions must be positive")
    ordered = sorted(normalized, key=lambda x: (-x["contributions"], x["label"].lower()))
    threshold = total * 0.5
    cumulative = 0
    decisive = []
    for item in ordered:
        cumulative += item["contributions"]
        decisive.append(item)
        if cumulative > threshold:
            break
    shares = [{**x, "share_percent": round(x["contributions"] / total * 100, 3)} for x in ordered]
    return {
        "schema_version": "0.1",
        "mode": "CONTRIBUTOR_ABSENCE_FACTOR",
        "metric": {
            "name": "Contributor Absence Factor",
            "authority": "CHAOSS",
            "threshold_rule": "smallest number of contributors whose cumulative supplied contributions exceed 50%",
            "value": len(decisive),
            "total_contributions": total,
            "decisive_contributors": [x["label"] for x in decisive],
            "contributor_shares": shares,
        },
        "interpretation": (
            "A low value is a concentration/risk conversation signal, not a judgment about contributors or proof the project is unhealthy."
        ),
        "limitations": [
            "The result depends entirely on the supplied contribution definition and time window.",
            "Commit count alone may miss review, issue triage, documentation, governance, release and community work.",
            "Use the metric with project context and data-ethics review; do not rank or shame individuals.",
        ],
        "execution": {"github_queried": False, "contributors_contacted": False, "repository_changed": False},
    }


def tokens(text: Any) -> set[str]:
    return {t.lower() for t in TOKEN.findall(str(text or "")) if t.lower() not in STOP and len(t) >= 3}


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return 0.0 if not union else len(a & b) / len(union)


def issue_dedupe(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("input must be an object")
    target = data.get("target")
    issues = data.get("issues")
    if not isinstance(target, dict) or not isinstance(issues, list):
        raise InputError("target object and issues array are required")
    target_number = target.get("number")
    if isinstance(target_number, bool) or not isinstance(target_number, int):
        raise InputError("target number must be integer")
    target_title = clean_label(target.get("title"), "target title", 500)
    target_title_tokens = tokens(target_title)
    target_all = target_title_tokens | tokens(target.get("body", ""))

    scored = []
    for item in issues:
        if not isinstance(item, dict):
            continue
        number = item.get("number")
        if isinstance(number, bool) or not isinstance(number, int) or number == target_number:
            continue
        title = clean_label(item.get("title"), f"issue {number} title", 500)
        title_score = jaccard(target_title_tokens, tokens(title))
        overall = jaccard(target_all, tokens(title) | tokens(item.get("body", "")))
        score = 0.7 * title_score + 0.3 * overall
        scored.append({
            "number": number,
            "title": title,
            "similarity": round(score, 4),
            "title_similarity": round(title_score, 4),
            "overall_similarity": round(overall, 4),
        })
    scored.sort(key=lambda x: (-x["similarity"], x["number"]))
    candidates = [x for x in scored if x["similarity"] >= 0.35][:10]
    return {
        "schema_version": "0.1",
        "mode": "ISSUE_DUPLICATE_PREFILTER",
        "target": {"number": target_number, "title": target_title},
        "candidates": candidates,
        "decision": "HUMAN_REVIEW_REQUIRED" if candidates else "NO_STRONG_LEXICAL_CANDIDATE",
        "automatic_duplicate_marking_allowed": False,
        "required_next_step": "Read candidate issue context and confirm equivalence before using GitHub's duplicate mechanism or posting a duplicate comment.",
        "limitations": [
            "Lexical similarity misses semantically equivalent reports that use different words and can over-rank shared templates/error boilerplate.",
            "This prefilter does not inspect attachments, code, logs, linked discussions, versions or reproduction details.",
            "Similarity is not proof of duplication; no issue is labeled, commented on or closed.",
        ],
        "execution": {"github_queried": False, "issue_changed": False, "comment_posted": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze sanitized maintenance metadata without repository mutation")
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("history", "absence", "dedupe"):
        p = sub.add_parser(mode)
        p.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.input)
        fn = {"history": history_explain, "absence": contributor_absence, "dedupe": issue_dedupe}[args.mode]
        result = fn(data)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
