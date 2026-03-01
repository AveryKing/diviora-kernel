from diviora_kernel.planning import create_plan
from diviora_kernel.schemas import DomainContract, StepResult, TaskRequest, TaskType
from diviora_kernel.verification import verify_run


def _task_with_contract() -> TaskRequest:
    return TaskRequest(
        task_id="dm-domain-1",
        title="Diviora offer + pricing",
        description="Decide Diviora's initial offer + pricing",
        task_type=TaskType.DECISION_MEMO,
        approval_mode="auto",
        domain_contract=DomainContract(
            domain_name="diviora_business_offer_pricing",
            required_concepts=["ICP", "offer", "pricing", "distribution"],
            option_required_fields=["Who it’s for", "What you deliver", "Pricing", "How you sell", "Why it wins"],
            recommendation_required_fields=["price points", "easiest to sell", "30 days"],
            evidence_policy="none",
        ),
    )


def test_drifting_memo_fails_domain_contract() -> None:
    task = _task_with_contract()
    plan = create_plan(task)

    drifting_memo = """
# Decision Memo

## Context
We are modernizing data systems and API layers.

## Options
- **Option 1: Stored procedure wrapper**
  - Who it’s for: Database team.
  - What you deliver: API facade.
  - Pricing: N/A.
  - How you sell: Internal roadmap.
  - Why it wins: Fewer migrations.
- **Option 2: Modular domain API**
  - Who it’s for: Platform team.
  - What you deliver: Service extraction.
  - Pricing: N/A.
  - How you sell: Architecture review.
  - Why it wins: Better contracts.
- **Option 3: Full replacement**
  - Who it’s for: Engineering leadership.
  - What you deliver: New service layer.
  - Pricing: N/A.
  - How you sell: Program approval.
  - Why it wins: Long-term flexibility.

## Recommendation
- **Recommend Option 2** because it balances migration risk.

## Risks / Tradeoffs
- Delivery complexity.

## Implementation Plan (phased)
1. Discovery.
2. Pilot.
3. Migration.

## Open Questions
- Which systems first?
""".strip()

    result = StepResult(
        step_id="step-1",
        success=True,
        status="completed",
        output_summary="ok",
        artifacts=["decision_memo.md"],
        metadata={"memo_content": drifting_memo},
    )
    verification = verify_run(plan=plan, step_results=[result], task=task)

    assert verification.passed is False
    assert any("Domain concept missing" in warning for warning in verification.warnings)


def test_valid_domain_contract_memo_passes() -> None:
    task = _task_with_contract()
    plan = create_plan(task)

    valid_memo = """
# Decision Memo

## Context
This memo aligns ICP, offer, pricing, and distribution choices for the first 30 days.

## Options
- **Option 1: Founder sprint**
  - Who it’s for: Founder-led B2B consultancies.
  - What you deliver: Offer design, one landing page, and outreach scripts.
  - Pricing: $1500 setup and $900/mo.
  - How you sell: Warm intros and outbound DMs.
  - Why it wins: Fast launch and clear proof point.
- **Option 2: Retainer model**
  - Who it’s for: Teams with existing pipeline.
  - What you deliver: Monthly conversion optimization cadence.
  - Pricing: $3000/mo.
  - How you sell: Funnel audit workshop.
  - Why it wins: Higher MRR.
- **Option 3: Advisory hybrid**
  - Who it’s for: Teams with in-house execution.
  - What you deliver: Weekly strategy + QA.
  - Pricing: $1000/mo advisory or $2400/mo hybrid.
  - How you sell: Diagnostic call and roadmap.
  - Why it wins: Flexible expansion path.

## Recommendation
- **Recommend Option 1** for fast first revenue.
- Exact price points: $1500 setup and $900/mo.
- This is easiest to sell in 30 days because it has a concrete scope and quick distribution channels.

## Risks / Tradeoffs
- Underpricing can reduce margin.

## Implementation Plan (phased)
1. Finalize ICP and offer.
2. Publish pricing and outreach assets.
3. Run distribution and close first clients.

## Open Questions
- Should referrals or outbound lead distribution first?
""".strip()

    result = StepResult(
        step_id="step-1",
        success=True,
        status="completed",
        output_summary="ok",
        artifacts=["decision_memo.md"],
        metadata={"memo_content": valid_memo},
    )
    verification = verify_run(plan=plan, step_results=[result], task=task)

    assert verification.passed is True


def test_option_required_fields_missing_fails() -> None:
    task = _task_with_contract()
    plan = create_plan(task)

    memo_missing_field = """
# Decision Memo

## Context
ICP offer pricing distribution are in scope.

## Options
- **Option 1: A**
  - Who it’s for: Segment A.
  - What you deliver: Package A.
  - Pricing: $1000/mo.
  - How you sell: Outbound.
- **Option 2: B**
  - Who it’s for: Segment B.
  - What you deliver: Package B.
  - Pricing: $2000/mo.
  - How you sell: Referrals.
  - Why it wins: Better retention.
- **Option 3: C**
  - Who it’s for: Segment C.
  - What you deliver: Package C.
  - Pricing: $3000/mo.
  - How you sell: Partnerships.
  - Why it wins: Better conversion.

## Recommendation
- **Recommend Option 2**.
- Exact price points: $2000/mo.
- This is easiest to sell in 30 days because channel fit is proven.

## Risks / Tradeoffs
- Risk.

## Implementation Plan (phased)
1. Plan.
2. Execute.
3. Iterate.

## Open Questions
- Question.
""".strip()

    result = StepResult(
        step_id="step-1",
        success=True,
        status="completed",
        output_summary="ok",
        artifacts=["decision_memo.md"],
        metadata={"memo_content": memo_missing_field},
    )
    verification = verify_run(plan=plan, step_results=[result], task=task)

    assert verification.passed is False
    assert any("missing required field" in warning.lower() for warning in verification.warnings)


def test_recommendation_without_price_points_fails() -> None:
    task = _task_with_contract()
    plan = create_plan(task)

    memo_no_price = """
# Decision Memo

## Context
This memo aligns ICP, offer, pricing, and distribution choices for launch.

## Options
- **Option 1: A**
  - Who it’s for: Segment A.
  - What you deliver: Package A.
  - Pricing: $1000/mo.
  - How you sell: Outbound.
  - Why it wins: Fast.
- **Option 2: B**
  - Who it’s for: Segment B.
  - What you deliver: Package B.
  - Pricing: $2000/mo.
  - How you sell: Referrals.
  - Why it wins: Better retention.
- **Option 3: C**
  - Who it’s for: Segment C.
  - What you deliver: Package C.
  - Pricing: $3000/mo.
  - How you sell: Partnerships.
  - Why it wins: Better conversion.

## Recommendation
- **Recommend Option 2** for stable growth.
- This is easiest to sell in 30 days because existing clients can be upsold.

## Risks / Tradeoffs
- Risk.

## Implementation Plan (phased)
1. Plan.
2. Execute.
3. Iterate.

## Open Questions
- Question.
""".strip()

    result = StepResult(
        step_id="step-1",
        success=True,
        status="completed",
        output_summary="ok",
        artifacts=["decision_memo.md"],
        metadata={"memo_content": memo_no_price},
    )
    verification = verify_run(plan=plan, step_results=[result], task=task)

    assert verification.passed is False
    assert any("price points" in warning.lower() for warning in verification.warnings)


def test_decision_memo_without_domain_contract_still_passes() -> None:
    task = TaskRequest(
        task_id="dm-no-contract-1",
        title="Decision memo",
        description="Verify backward compatibility",
        task_type=TaskType.DECISION_MEMO,
        approval_mode="auto",
    )
    plan = create_plan(task)

    valid_memo = """
# Decision Memo

## Context
A context section.

## Options
- Option A
- Option B
- Option C

## Recommendation
- Option B

## Risks / Tradeoffs
- Some risk.

## Implementation Plan (phased)
1. Phase one.
2. Phase two.

## Open Questions
- Unresolved question.
""".strip()

    result = StepResult(
        step_id="step-1",
        success=True,
        status="completed",
        output_summary="ok",
        artifacts=["decision_memo.md"],
        metadata={"memo_content": valid_memo},
    )
    verification = verify_run(plan=plan, step_results=[result], task=task)

    assert verification.passed is True
