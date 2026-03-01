# Decision Memo

## Context
This memo evaluates Options + risks for adding an API layer to phase out stored procedures in a PHP 8.3 system; include pragmatic path, tech options, and migration plan. and frames practical choices for delivery in the current operating constraints.

## Options
- **Option 1: Wrap existing stored procedures behind a thin API facade.** Lowest migration risk, fast onboarding path.
- **Option 2: Introduce a modular domain API with selective service extraction.** Balanced modernization with controlled rewrite scope.
- **Option 3: Full service-layer replacement of stored procedures.** Highest long-term flexibility, highest delivery risk and lead time.

## Recommendation
- **Recommend Option 2** as the pragmatic path: it enables progressive decoupling while preserving production stability.

## Risks / Tradeoffs
- Transitional complexity while API contracts stabilize.
- Temporary dual-maintenance overhead across procedure and API layers.
- Potential performance regressions unless query hot paths are benchmarked early.

## Implementation Plan (phased)
1. **Phase 1 - Discovery and Contracting:** inventory procedures, define API boundaries, agree success metrics.
2. **Phase 2 - Pilot and Hardening:** migrate one bounded domain to the API layer, add observability and regression tests.
3. **Phase 3 - Progressive Migration:** expand by domain, retire replaced procedures, and enforce new API-first standards.

## Open Questions
- Which domains deliver the best migration ROI in the first two quarters?
- What SLO baselines should gate each migration phase?
- How should ownership transition between DB-heavy and API teams be sequenced?
