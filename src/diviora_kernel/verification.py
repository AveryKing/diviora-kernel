from __future__ import annotations

import string

from diviora_kernel.schemas import DomainContract, Plan, StepResult, TaskRequest, TaskType, VerificationResult

_REQUIRED_DECISION_MEMO_SECTIONS = [
    "Context",
    "Options",
    "Recommendation",
    "Risks / Tradeoffs",
    "Implementation Plan (phased)",
    "Open Questions",
]
_PRICE_HINT_TOKENS = {"$", "usd", "/mo", "per", "month", "setup"}
_EASIEST_30_DAY_CONCEPT = "easiest to sell in 30 days"


def verify_run(
    plan: Plan,
    step_results: list[StepResult],
    task: TaskRequest | None = None,
) -> VerificationResult:
    checks: list[str] = []
    warnings: list[str] = []

    planned_ids = {step.step_id for step in plan.steps}
    result_ids = {result.step_id for result in step_results}

    missing = sorted(planned_ids - result_ids)
    if missing:
        warnings.append(f"Missing results for steps: {', '.join(missing)}")
    else:
        checks.append("Every planned step has a recorded result")

    failed = [result.step_id for result in step_results if not result.success]
    if failed:
        warnings.append(f"Failed steps: {', '.join(failed)}")
    else:
        checks.append("All executed steps reported success")

    task_type = getattr(task.task_type, "value", task.task_type) if task else None
    if task_type == TaskType.DECISION_MEMO.value:
        decision_issues = _verify_decision_memo(step_results, task.domain_contract if task else None)
        if decision_issues:
            warnings.extend(decision_issues)
        else:
            checks.append("Decision memo passed strict section, recommendation, and domain checks")

    passed = not missing and not failed and not warnings
    return VerificationResult(passed=passed, checks=checks, warnings=warnings)


def _verify_decision_memo(step_results: list[StepResult], domain_contract: DomainContract | None) -> list[str]:
    memo_text = ""
    for result in step_results:
        if "decision_memo.md" in result.artifacts:
            memo_text = str(result.metadata.get("memo_content", ""))
            break

    if not memo_text:
        return ["Missing decision_memo.md artifact content"]

    issues: list[str] = []
    sections = _extract_sections(memo_text)

    required_sections = domain_contract.required_sections if domain_contract and domain_contract.required_sections else _REQUIRED_DECISION_MEMO_SECTIONS

    for section in required_sections:
        if section not in sections:
            issues.append(f"Decision memo missing required section: {section}")

    options_body = sections.get("Options", "")
    option_blocks = _extract_option_blocks(options_body)
    top_level_options = _count_top_level_bullets(options_body)
    if top_level_options < 3:
        issues.append("Decision memo Options section must include at least 3 options")

    recommendation_body = sections.get("Recommendation", "")
    recommendation_option_refs = _count_option_references(recommendation_body)
    if recommendation_option_refs != 1:
        issues.append("Decision memo Recommendation must contain exactly one option")

    if domain_contract:
        issues.extend(_verify_domain_contract(memo_text, sections, option_blocks, recommendation_body, domain_contract))

    return issues


def _verify_domain_contract(
    memo_text: str,
    sections: dict[str, str],
    option_blocks: list[tuple[str, list[str]]],
    recommendation_body: str,
    domain_contract: DomainContract,
) -> list[str]:
    issues: list[str] = []
    tokenized = _tokenize_with_positions(memo_text)
    heading_tokens = _heading_tokens(memo_text)

    for concept in domain_contract.required_concepts:
        if not _match_concept(concept, tokenized, heading_tokens):
            issues.append(f"Domain concept missing from memo: {concept}")

    if domain_contract.option_required_fields:
        if len(option_blocks) < 3:
            issues.append("Domain contract requires structured option blocks with field labels")
        for option_title, option_lines in option_blocks:
            option_text = "\n".join(option_lines)
            for required_field in domain_contract.option_required_fields:
                normalized_required = _normalize_text(required_field)
                field_present = False
                for line in option_text.splitlines():
                    stripped = line.strip()
                    if not stripped.startswith('- '):
                        continue
                    if ':' not in stripped:
                        continue
                    label_text = stripped[2:].split(':', 1)[0]
                    if _normalize_text(label_text) == normalized_required:
                        field_present = True
                        break
                if not field_present:
                    issues.append(f"Option '{option_title}' missing required field: {required_field}")

    if domain_contract.recommendation_required_fields:
        if not _contains_price_pattern(recommendation_body):
            issues.append("Recommendation must include explicit price points")
        if not _match_concept(_EASIEST_30_DAY_CONCEPT, _tokenize_with_positions(recommendation_body), set()):
            issues.append("Recommendation must explain why this is easiest to sell in 30 days")

    if domain_contract.evidence_policy == "citations_or_unknown":
        issues.extend(_verify_evidence_policy(sections))

    return issues


def _verify_evidence_policy(sections: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for section_name, body in sections.items():
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(("#", "-", "*", "1.", "2.", "3.", "4.", "5.")):
                continue
            if len(stripped.split()) < 8:
                continue
            if stripped.endswith("UNKNOWN"):
                continue
            if stripped.endswith(")") and "(Source:" in stripped:
                continue
            issues.append(f"Evidence policy violation in section '{section_name}': {stripped}")
    return issues


def _extract_sections(memo_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None

    for raw_line in memo_text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
            continue

        if current is not None:
            existing = sections[current]
            sections[current] = f"{existing}\n{raw_line}" if existing else raw_line

    return sections


def _extract_option_blocks(options_body: str) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []

    for raw_line in options_body.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- **Option"):
            if current_title:
                blocks.append((current_title, current_lines))
            current_title = stripped
            current_lines = []
            continue
        if current_title:
            current_lines.append(raw_line)

    if current_title:
        blocks.append((current_title, current_lines))

    return blocks


def _normalize_text(text: str) -> str:
    table = str.maketrans({ch: " " for ch in string.punctuation if ch != "$"})
    normalized = text.lower().translate(table)
    return " ".join(normalized.split())


def _tokenize_with_positions(text: str) -> list[str]:
    normalized = _normalize_text(text)
    return normalized.split()


def _heading_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw_line in text.splitlines():
        if raw_line.strip().startswith("## "):
            tokens.update(_tokenize_with_positions(raw_line[3:]))
    return tokens


def _match_concept(concept: str, doc_tokens: list[str], heading_tokens: set[str], window: int = 10) -> bool:
    concept_tokens = _tokenize_with_positions(concept)
    if not concept_tokens:
        return True

    if all(token in heading_tokens for token in concept_tokens):
        return True

    token_positions: dict[str, list[int]] = {}
    for idx, token in enumerate(doc_tokens):
        token_positions.setdefault(token, []).append(idx)

    if any(token not in token_positions for token in concept_tokens):
        return False

    candidate_positions = token_positions[concept_tokens[0]]
    for anchor in candidate_positions:
        lower = max(anchor - window, 0)
        upper = min(anchor + window + 1, len(doc_tokens))
        local_tokens = set(doc_tokens[lower:upper])
        if all(token in local_tokens for token in concept_tokens):
            return True

    return False




def _count_top_level_bullets(section_body: str) -> int:
    count = 0
    for raw_line in section_body.splitlines():
        stripped = raw_line.lstrip()
        indent = len(raw_line) - len(stripped)
        if indent == 0 and stripped.startswith("- "):
            count += 1
    return count


def _count_option_references(section_body: str) -> int:
    count = 0
    for line in section_body.splitlines():
        normalized = _normalize_text(line)
        count += normalized.split().count("option")
    return count

def _contains_price_pattern(text: str) -> bool:
    lower = text.lower()
    if "$" in text:
        return True
    if "usd" in lower:
        return True
    if "/mo" in lower:
        return True
    if "per month" in lower:
        return True
    if "setup" in lower:
        return True
    return False
