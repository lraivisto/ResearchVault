import json

import scripts.core as core
import scripts.strategy as strategy


def test_strategy_recommends_verify_plan_when_low_confidence_and_no_queue(db_conn):
    core.start_project("p1", "Project 1", "Objective")
    core.add_insight("p1", "Dubious claim", "Needs corroboration.", tags="", confidence=0.4)

    state = strategy.analyze_project_state("p1")
    rec = strategy.recommend_next_best_action(state)

    assert rec.action == "VERIFY_PLAN"


def test_strategy_recommends_verify_run_when_queue_exists(db_conn):
    core.start_project("p1", "Project 1", "Objective")
    core.add_insight("p1", "Dubious claim", "Needs corroboration.", tags="unverified", confidence=0.4)

    missions = core.plan_verification_missions("p1", threshold=0.7, max_missions=5)
    assert missions

    state = strategy.analyze_project_state("p1")
    rec = strategy.recommend_next_best_action(state)

    assert rec.action == "VERIFY_RUN"


def test_strategy_recommends_synthesis_when_density_is_high(db_conn):
    core.start_project("p1", "Project 1", "Objective")
    for i in range(8):
        core.add_insight("p1", f"Finding {i}", f"Content {i}", tags="solid", confidence=0.95)

    state = strategy.analyze_project_state("p1")
    rec = strategy.recommend_next_best_action(state)

    assert rec.action == "SYNTHESIZE"


def test_strategy_recommends_scuttle_when_evidence_is_thin(db_conn):
    core.start_project("p1", "Project 1", "Rising underground bands Finland")

    state = strategy.analyze_project_state("p1")
    rec = strategy.recommend_next_best_action(state)

    assert rec.action == "SCUTTLE"


def test_strategize_execute_includes_execution_block(db_conn):
    core.start_project("p1", "Project 1", "Objective")
    core.add_insight("p1", "Dubious claim", "Needs corroboration.", tags="unverified", confidence=0.4)

    out = strategy.strategize("p1", execute=True)
    assert out["recommendation"]["action"] == "VERIFY_PLAN"
    assert out["execution"]["ok"] is True
    assert out["execution"]["details"]["missions_created"] >= 1

    # Ensure JSON serialization is stable (CLI uses JSON output).
    json.dumps(out, ensure_ascii=True)

