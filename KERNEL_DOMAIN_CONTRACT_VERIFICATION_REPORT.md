# Kernel Domain Contract Verification Report

## Drift observed and why old checks missed it

The prior decision memo verifier only enforced document format:
- required sections existed,
- there were at least three bullets under options,
- and recommendation had exactly one bullet.

That allowed topical drift. A memo could be perfectly formatted while answering a different domain (for example engineering migration options instead of business offer + pricing). The verifier lacked deterministic domain-semantic checks.

## DomainContract mechanism

A new optional `DomainContract` is now part of `TaskRequest` and can be supplied for decision memo tasks.

`DomainContract` captures auditable constraints:
- `domain_name`
- `required_sections`
- `required_concepts`
- `option_required_fields`
- `recommendation_required_fields`
- `evidence_policy`
- `rubric`

When provided, the verifier applies these deterministic checks in addition to structural checks.

## Deterministic enforcement now in place

### Baseline decision memo checks
- Required top-level sections must exist.
- Options must contain at least 3 options.
- Recommendation must contain exactly one recommended option bullet.

### Domain alignment checks
- **Concept matching (no blacklist):**
  - Normalize text to lowercase and stripped punctuation.
  - Tokenize concepts and memo text.
  - Concept passes only if all concept tokens appear within a bounded token window, or all concept tokens appear in headings.
- **Option field completeness:**
  - Each option block must include each required labeled sub-bullet field.
  - Missing one required field in any option fails verification.
- **Recommendation sufficiency:**
  - Recommendation must include explicit price pattern signal (`$`, `USD`, `/mo`, `per month`, `setup`).
  - Recommendation must include deterministic match for “easiest to sell in 30 days”.
- **Evidence policy (`citations_or_unknown`)**:
  - Non-trivial plain claim lines must end with `(Source: ...)` or `UNKNOWN`.

All checks are deterministic string/token/pattern logic. No LLM judgment is used in verification.

## Planning and generation support

- Planning now includes domain contract context in decision memo prompts.
- LLM decision memo generation supports a domain-contract-aware template that emits:
  - domain-focused context,
  - options with required sub-fields,
  - recommendation with explicit price points and 30-day sellability rationale.

## Extending to other domains

To support another domain, define a `DomainContract` tailored to that domain:
1. Set domain-specific required concepts.
2. Define option and recommendation required fields.
3. Optionally define required sections and rubric.
4. Enable stricter evidence policy where needed.

Because constraints are declarative and deterministic, extension is auditable and repeatable without changing verifier architecture.
