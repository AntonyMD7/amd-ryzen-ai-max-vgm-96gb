#!/usr/bin/env python3
"""DAIS P-058 Dangerous-Script Detector.

Static, non-executing lexical risk detector for selected script/config files.
It intentionally does not execute repository code, invoke a shell, fetch network
content, or claim complete security analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

VERSION = "0.12.0"
ROADMAP_ID = "P-058"
MAX_FILES = 5000
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024

SUPPORTED_SUFFIXES = {
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ksh": "shell",
    ".ps1": "powershell",
    ".psm1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    ".yml": "yaml",
    ".yaml": "yaml",
}

SEVERITY_ORDER = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class UnsafeInput(ValueError):
    """Input cannot be scanned within the bounded contract."""


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    category: str
    languages: frozenset[str]
    pattern: re.Pattern[str]
    rationale: str


def _rule(
    rule_id: str,
    severity: str,
    category: str,
    languages: Iterable[str],
    pattern: str,
    rationale: str,
) -> Rule:
    return Rule(
        rule_id=rule_id,
        severity=severity,
        category=category,
        languages=frozenset(languages),
        pattern=re.compile(pattern, re.IGNORECASE),
        rationale=rationale,
    )


RULES: tuple[Rule, ...] = (
    _rule(
        "DS001",
        "CRITICAL",
        "remote-code-execution",
        {"shell", "yaml"},
        r"\b(?:curl|wget)\b[^\n|]{0,500}\|\s*(?:sudo\s+)?(?:sh|bash|zsh|ksh)\b",
        "Remote content is piped directly into a shell.",
    ),
    _rule(
        "DS002",
        "CRITICAL",
        "remote-code-execution",
        {"powershell", "yaml"},
        r"\b(?:invoke-webrequest|iwr|wget|curl|downloadstring)\b.{0,500}\b(?:invoke-expression|iex)\b",
        "Downloaded content is coupled to PowerShell expression execution.",
    ),
    _rule(
        "DS003",
        "CRITICAL",
        "obfuscated-execution",
        {"powershell", "batch", "yaml"},
        r"\bpowershell(?:\.exe)?\b[^\n]{0,500}(?:-(?:enc|encodedcommand)\b|-e\s+[A-Za-z0-9+/=]{20,})",
        "Encoded PowerShell execution can obscure the command being run.",
    ),
    _rule(
        "DS010",
        "HIGH",
        "destructive-filesystem",
        {"shell", "yaml"},
        r"(?:^|[;&|]\s*|\s)\brm\s+(?=[^\n]*-[A-Za-z]*r)(?=[^\n]*-[A-Za-z]*f)[^\n]{0,200}\s/(?:\s|$|\*|['\"])",
        "Recursive forced deletion targets a filesystem-root path.",
    ),
    _rule(
        "DS011",
        "HIGH",
        "destructive-storage",
        {"shell", "powershell", "batch", "yaml"},
        r"\b(?:mkfs(?:\.[A-Za-z0-9_-]+)?|clear-disk|initialize-disk)\b|(?:^|\s)format(?:\.com)?\s+[A-Za-z]:",
        "The command can format or initialize storage.",
    ),
    _rule(
        "DS012",
        "HIGH",
        "raw-disk-write",
        {"shell", "yaml"},
        r"\bdd\b[^\n]{0,500}\bof=/dev/(?:sd[a-z]\d*|nvme\d+n\d+(?:p\d+)?|vd[a-z]\d*|xvd[a-z]\d*)\b",
        "dd writes directly to a block device.",
    ),
    _rule(
        "DS013",
        "HIGH",
        "dynamic-execution",
        {"shell", "powershell", "yaml"},
        r"(?:^|[;&|]\s*|\s)\beval\b\s+|\b(?:invoke-expression|iex)\b\s+",
        "Dynamic expression execution can turn data into code.",
    ),
    _rule(
        "DS014",
        "HIGH",
        "privileged-mutation",
        {"shell", "yaml"},
        r"\b(?:sudo|doas)\b[^\n]{0,300}\b(?:rm|mkfs|dd|systemctl|service|apt(?:-get)?|dnf|yum|pacman|zypper)\b",
        "A privileged command performs mutation or package/service control.",
    ),
    _rule(
        "DS015",
        "HIGH",
        "service-mutation",
        {"shell", "yaml"},
        r"\b(?:systemctl|service)\s+(?:stop|disable|mask|restart|start|enable)\b",
        "The command changes service state.",
    ),
    _rule(
        "DS016",
        "HIGH",
        "registry-mutation",
        {"powershell", "batch", "yaml"},
        r"\breg(?:\.exe)?\s+(?:add|delete)\b|\b(?:remove-itemproperty|set-itemproperty)\b",
        "The command mutates the Windows registry.",
    ),
    _rule(
        "DS017",
        "HIGH",
        "firewall-weakening",
        {"shell", "powershell", "batch", "yaml"},
        r"\bufw\s+(?:disable|reset)\b|\biptables\b[^\n]{0,300}\s-F\b|\bnft\b[^\n]{0,300}\bflush\b|\bset-netfirewallprofile\b[^\n]{0,300}-enabled\s+\$?false\b",
        "The command can disable or flush firewall policy.",
    ),
    _rule(
        "DS018",
        "HIGH",
        "permission-weakening",
        {"shell", "yaml"},
        r"\bchmod\s+(?:-R\s+)?(?:0?777|a\+rwx)\b",
        "World-writable/executable permissions materially weaken access controls.",
    ),
    _rule(
        "DS019",
        "HIGH",
        "execution-policy-bypass",
        {"powershell", "batch", "yaml"},
        r"\bpowershell(?:\.exe)?\b[^\n]{0,300}-(?:executionpolicy|ep)\s+bypass\b",
        "PowerShell execution-policy bypass reduces a defense-in-depth barrier.",
    ),
    _rule(
        "DS030",
        "MEDIUM",
        "destructive-git",
        {"shell", "powershell", "batch", "yaml"},
        r"\bgit\s+(?:reset\s+--hard|clean\s+-[A-Za-z]*f[A-Za-z]*d[A-Za-z]*x?|push\b[^\n]{0,200}(?:--force|-f)\b|branch\s+-D)\b",
        "The Git command can discard local state or rewrite remote history.",
    ),
    _rule(
        "DS031",
        "MEDIUM",
        "package-mutation",
        {"shell", "yaml"},
        r"\b(?:apt(?:-get)?|dnf|yum|pacman|zypper)\s+(?:install|remove|purge|upgrade|dist-upgrade|update)\b",
        "The command changes installed packages or package metadata.",
    ),
    _rule(
        "DS032",
        "MEDIUM",
        "forced-process-termination",
        {"shell", "powershell", "batch", "yaml"},
        r"\bkill\s+-9\b|\btaskkill(?:\.exe)?\b[^\n]{0,300}\s/F\b|\bstop-process\b[^\n]{0,300}-force\b",
        "Forced process termination may cause data loss or service interruption.",
    ),
    _rule(
        "DS033",
        "MEDIUM",
        "recursive-delete",
        {"shell", "yaml"},
        r"(?:^|[;&|]\s*|\s)\brm\s+(?=[^\n]*-[A-Za-z]*r)(?=[^\n]*-[A-Za-z]*f)\b",
        "Recursive forced deletion deserves explicit review even away from root.",
    ),
    _rule(
        "DS034",
        "MEDIUM",
        "scheduled-persistence",
        {"shell", "powershell", "batch", "yaml"},
        r"\b(?:crontab|register-scheduledtask)\b|\bschtasks(?:\.exe)?\b[^\n]{0,300}/create\b",
        "The command creates or modifies scheduled execution.",
    ),
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _relative_root(workspace: Path, requested: str) -> Path:
    if not requested or "\x00" in requested:
        raise UnsafeInput("root is empty or contains NUL")
    requested_path = Path(requested)
    if requested_path.is_absolute() or any(part == ".." for part in requested_path.parts):
        raise UnsafeInput("root must be a contained relative path")
    workspace = workspace.resolve(strict=True)
    candidate = workspace
    for part in requested_path.parts:
        if part in ("", "."):
            continue
        candidate = candidate / part
        if candidate.is_symlink():
            raise UnsafeInput("root path contains a symlink")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise UnsafeInput("root escapes workspace") from exc
    if not resolved.is_dir():
        raise UnsafeInput("root must be a directory")
    return resolved


def _language_for(path: Path, root: Path) -> str | None:
    suffix = path.suffix.lower()
    language = SUPPORTED_SUFFIXES.get(suffix)
    if language != "yaml":
        return language
    rel = path.relative_to(root).as_posix().lower()
    if rel.startswith(".github/workflows/") or rel.endswith("/action.yml") or rel.endswith("/action.yaml") or rel in {"action.yml", "action.yaml"}:
        return "yaml"
    return None


def _iter_candidates(root: Path) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in {".git", ".venv", "node_modules"} and not (current_path / d).is_symlink())
        for name in sorted(files):
            path = current_path / name
            language = _language_for(path, root)
            if language is None:
                continue
            if path.is_symlink():
                raise UnsafeInput("script/config candidate is a symlink")
            if not path.is_file():
                raise UnsafeInput("script/config candidate is not a regular file")
            candidates.append((path, language))
            if len(candidates) > MAX_FILES:
                raise UnsafeInput(f"candidate count exceeds {MAX_FILES}")
    return candidates


def _read_text(path: Path) -> tuple[str, int]:
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise UnsafeInput(f"candidate exceeds {MAX_FILE_BYTES} bytes")
    data = path.read_bytes()
    if b"\x00" in data:
        raise UnsafeInput("candidate contains NUL/binary data")
    try:
        return data.decode("utf-8"), len(data)
    except UnicodeDecodeError as exc:
        raise U[њШY™R[њ]
Ш[™Y]H\И›ЭU‹N^ЉHњ›ЫH^В‚‚™Y€Щљ[™[™ЬЧЩ›Ь—Э^
^€Э‹[™ЭXYЩN€Э‹™[Ь]€ЭЉHO€\ЭЩXЭЬЭ‹Шљ™XЭWN‚€]Ъ\ЪHЪLЌM—Э^
™[Ь]
B€љ[™[™ЬО€\ЭЩXЭЬЭ‹Шљ™XЭWHHЧB€›Ь€[™WЫќ[X™\‹[™H[€[ќ[Y\]J^њЬ][™\К
KЭ\ќLJN‚€›Ь€ќ[H[€•STО‚€Y€[™ЭXYЩH›Э[€ќ[K›[™ЭXYЩ\О‚€ЫЫќ[ќYB€Y€ќ[Kњ]\›‹њЩX\Ъ
[™JN‚€љ[™[™ЬЛ\[™
€В€њќ[WЪYЋ€ќ[Kњќ[WЪY€њЩ]™\љ]HЋ€ќ[KњЩ]™\љ]K€Ш]YЫЬћHЋ€ќ[KШ]YЫЬћK€›[™ЭXYЩHЋ€[™ЭXYЩK€њ]ЬЪLЌM€Ћ€]Ъ\Ъ€›[™WЫќ[X™\€Ћ€[™WЫќ[X™\‹€›[™WЬЪLЌM€Ћ€ЪLЌM—Э^
[™JK€њ][Ы[HЋ€ќ[Kњ][Ы[K€B€
B€љ[™[™ЬЛњЫЬќ
€Щ^O[[X™H][N€
€TСU‘T’UWУФ‘T–ЬЭЉ][VИњЩ]™\љ]H—JWK€ЭЉ][VИњќ[WЪY—JK€ЭЉ][VИњ]ЬЪLЌM€—JK€[ќ
][VИ›[™WЫќ[X™\€—JK€
B€
B€™]\›€љ[™[™ЬВ‚‚™Y€ШШ[ЉЫЬљЬЬXЩN€]™\]Y\ЭYЬ›ЫЭ€Э€H‹€ЉHO€XЭЬЭ‹Шљ™XЭN‚€›ЫЭHЬ™[]]™WЬ›ЫЭ
ЫЬљЬЬXЩK™\]Y\ЭYЬ›ЫЭ
B€Ш[™Y]\ИHЪ]\—ШШ[™Y]\К›ЫЭ
B€Э[Шћ]\ИH€[Щљ[™[™ЬО€\ЭЩXЭЬЭ‹Шљ™XЭWHHЧB€[™ЭXYЩWШЫЭ[ќО€XЭЬЭ‹[ќHHЯB€›Ь€][™ЭXYЩH[€Ш[™Y]\О‚€^Ъ^™HHЬ™XYЭ^
]
B€Э[Шћ]\И
ПHЪ^™B€Y€Э[Шћ]\И€PVХХSР–UTО‚€Z\ЩH[њШY™R[њ]
€YЩЬ™YШ]HШ[™Y]Hћ]\И^ЩYYУPVХХSР–UTЯHЉB€[™ЭXYЩWШЫЭ[ќЦЫ[™ЭXYЩWHH[™ЭXYЩWШЫЭ[ќЛ™Щ]
[™ЭXYЩK
H
ИB€™[H]њ™[]]™WЭК›ЫЭ
K\ЧЬЬЪ^

B€[Щљ[™[™ЬЛ™^[™
Щљ[™[™ЬЧЩ›Ь—Э^
^[™ЭXYЩK™[
JB‚€Щ]™\љ]WШЫЭ[ќИHЬЩ]™\љ]N€›Ь€Щ]™\љ]H[€
ђФ’UPРS‹’QТ‹“QQUSHЉ_B€›Ь€љ[™[™И[€[Щљ[™[™ЬО‚€Щ]€HЭЉљ[™[™ЦИњЩ]™\љ]H—JB€Y€Щ]€[€Щ]™\љ]WШЫЭ[ќО‚€Щ]™\љ]WШЫЭ[ќЦЬЩ]—H
ПHB‚€YЪ\ЭH““У‘H‚€Y€[Щљ[™[™ЬО‚€YЪ\ЭHX^

ЭЉ–ИњЩ]™\љ]H—JH›Ь€€[€[Щљ[™[™ЬКKЩ^OTСU‘T’UWУФ‘T‹—ЧЩЩ]][WЧКB‚€Э]\ИH”TФИ€Y€›Э[Щљ[™[™ЬИ[ЩH”‘U’QUЧФ‘TURT‘Q‚€™]\›€В€њШЪ[XWЭ™\њЪ[Ы€Ћ€ЊKЊ‹€њ›ШYX\ЪYЋ€“РQPTТQ€њ›ЩXЭЭ™\њЪ[Ы€Ћ€‘T”ТSУ‹€њЭ]\ИЋ€Э]\Л€љYЪ\ЭЬЩ]™\љ]HЋ€YЪ\Э€™љ[\ЧЬШШ[›™YЋ€[ЉШ[™Y]\КK€ћ]\ЧЬШШ[›™YЋ€Э[Шћ]\Л€›[™ЭXYЩWШЫЭ[ќИЋ€XЭ
ЫЬќY
[™ЭXYЩWШЫЭ[ќЛљ][\К
JJK€™љ[™[™ЧШЫЭ[ќЋ€[Љ[Щљ[™[™ЬКK€њЩ]™\љ]WШЫЭ[ќИЋ€Щ]™\љ]WШЫЭ[ќЛ€™љ[™[™ЬИЋ€[Щљ[™[™ЬЛ€њљ]XЮHЋ€В€њЫЭ\ЩWЭ^Ь™]Z[™YЋ€[ЩK€›X]ЪYЭ^Ь™]Z[™YЋ€[ЩK€XњЫЫ]WЬ]ЧЬ™]Z[™YЋ€[ЩK€Ь™Y[ќX[ЧЬ™]Z[™YЋ€[ЩK€K€ЫZ[\ИЋ€В€њ™\ЬЪ]ЬћWЬШY™HЋ€[ЩK€њШЬљ\ЬШY™WЭЧЩ^XЭ]HЋ€[ЩK€[Щ[™Щ\›Э\ЧШ™Z]љ[Ь—Щ]XЭYЋ€[ЩK€њЩ[X[ќXЧЬЭ]XЧШ[[\Ъ\ЧШЫЫ\]HЋ€[ЩK€K€B‚‚™Y€ЭЬљ]WЪњЫЫЉ]€]]N€XЭЬЭ‹Шљ™XЭJHO€›Ы™N‚€]њ\™[ќ›ZЩ\Љ\™[ќПUќYK^\ЭЫЪПUќYJB€]ќЬљ]WЭ^
њЫЫ‹™[\К]K[™[ќL‹ЫЬќЪЩ^\ПUќYJH
И—€‹[ЫЩ[™ПHќ]‹NЉB‚‚™Y€XZ[Љ
HO€[ќ‚€\њЩ\€H\™Ь\њЩKђ\™Э[Y[ќ\њЩ\Љ\ШЬљ\[ЫЏH‘RTИLN[™Щ\›Э\ЛTШЬљ\]XЭЬ€ЉB€\њЩ\‹YШ\™Э[Y[ќ
‹K]ЫЬљЬЬXЩH‹™\]Z\™YUќYJB€\њЩ\‹YШ\™Э[Y[ќ
‹K\›ЫЭ‹Y][H‹€ЉB€\њЩ\‹YШ\™Э[Y[ќ
‹K[Э]]‹™\]Z\™YUќYJB€\™ЬИH\њЩ\‹њ\њЩWШ\™ЬК
B‚€ћN‚€™\ЬќHШШ[Љ]
\™ЬЛќЫЬљЬЬXЩJK\™ЬЛњ›ЫЭ
B€^Щ\
ФС\њ›Ь‹[њШY™R[њ]
H\И^О‚€\њ›Ь€HВ€њШЪ[XWЭ™\њЪ[Ы€Ћ€ЊKЊ‹€њ›ШYX\ЪYЋ€“РQPTТQ€њ›ЩXЭЭ™\њЪ[Ы€Ћ€‘T”ТSУ‹€њЭ]\ИЋ€‘T”“Ф€‹€™\њ›Ь—ШЫ\ЬИЋ€^Л—ЧШЫ\ЬЧЧЛ—ЧЫ[YWЧЛ€њљ]XЮHЋ€В€њЫЭ\ЩWЭ^Ь™]Z[™YЋ€[ЩK€›X]ЪYЭ^Ь™]Z[™YЋ€[ЩK€XњЫЫ]WЬ]ЧЬ™]Z[™YЋ€[ЩK€Ь™Y[ќX[ЧЬ™]Z[™YЋ€[ЩK€K€ЫZ[\ИЋ€В€њ™\ЬЪ]ЬћWЬШY™HЋ€[ЩK€њШЬљ\ЬШY™WЭЧЩ^XЭ]HЋ€[ЩK€[Щ[™Щ\›Э\ЧШ™Z]љ[Ь—Щ]XЭYЋ€[ЩK€њЩ[X[ќXЧЬЭ]XЧШ[[\Ъ\ЧШЫЫ\]HЋ€[ЩK€K€B€ЭЬљ]WЪњЫЫЉ]
\™ЬЛ›Э]]
K\њ›ЬЉB€љ[ќ
”NФХUTПQT”“Ф€ЉB€™]\›€B‚€ЭЬљ]WЪњЫЫЉ]
\™ЬЛ›Э]]
K™\Ьќ
B€љ[ќ
€”NФХUTП^Ь™\ЬќЙЬЭ]\ЙЧ_HЉB€љ[ќ
€”NС’STЧФРРS“‘Q^Ь™\ЬќЙЩљ[\ЧЬШШ[›™Y	Ч_HЉB€љ[ќ
€”NС’S‘S‘ЧРУХS•^Ь™\ЬќЙЩљ[™[™ЧШЫЭ[ќ	Ч_HЉB€љ[ќ
€”NТQТTХФСU‘T’UO^Ь™\ЬќЙЪYЪ\ЭЬЩ]™\љ]IЧ_HЉB€™]\›€‚‚љY€ЧЫ[YWЧИOH—ЧЫXZ[—ЧИЋ‚€Z\ЩHЮ\Э[Q^]
XZ[Љ
JB