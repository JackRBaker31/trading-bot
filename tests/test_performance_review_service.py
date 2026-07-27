import json
import sqlite3
from datetime import datetime, timedelta, timezone

from app.performance_review_service import PerformanceReviewService


def create_database(path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript("""
        CREATE TABLE jobs (job_id TEXT, job_type TEXT, status TEXT, created_at TEXT, started_at TEXT, finished_at TEXT, payload_json TEXT, result_json TEXT, error_code TEXT, error_summary TEXT, idempotency_key TEXT);
        CREATE TABLE run_history (run_id TEXT, run_type TEXT, status TEXT, started_at TEXT, finished_at TEXT, provider TEXT, symbols_json TEXT, created_count INTEGER, skipped_count INTEGER, failure_count INTEGER, error_code TEXT, error_summary TEXT, metadata_json TEXT);
        CREATE TABLE shadow_decisions (decision_id TEXT, article_id TEXT, symbol TEXT, created_at TEXT, model_version TEXT, action TEXT, score REAL, confidence REAL, sentiment TEXT, event_type TEXT, is_material INTEGER, headline TEXT, eligible_for_trade INTEGER, reasons_json TEXT, blocking_reasons_json TEXT, reference_price REAL, reference_captured_at TEXT);
        CREATE TABLE decision_memory (decision_id TEXT, fingerprint TEXT, captured_at TEXT, thesis_generated_at TEXT, symbol TEXT, recommendation TEXT, score REAL, confidence REAL, confidence_coverage REAL, risk_tier TEXT, time_horizon TEXT, suggested_position_value REAL, eligible_for_execution INTEGER, headline TEXT, primary_driver TEXT, capabilities_json TEXT, reasons_json TEXT, blockers_json TEXT, warnings_json TEXT, executed INTEGER, paper_trade_id TEXT);
        CREATE TABLE copilot_decision_snapshots (snapshot_id TEXT, captured_at TEXT, overall_status TEXT, platform_status TEXT, trading_readiness TEXT, market_outlook TEXT, confidence REAL, signal_count INTEGER, actionable_signal_count INTEGER, evidence_quality TEXT, graduation_ready INTEGER, graduation_passed_checks INTEGER, graduation_total_checks INTEGER, graduation_failed_checks INTEGER, decision TEXT, blockers_json TEXT);
        CREATE TABLE decision_outcomes (outcome_id TEXT, decision_id TEXT, symbol TEXT, horizon_days INTEGER, target_date TEXT, observed_at TEXT, entry_price REAL, observed_price REAL, absolute_return REAL, benchmark_symbol TEXT, benchmark_entry_price REAL, benchmark_observed_price REAL, benchmark_return REAL, alpha REAL, maximum_favourable_excursion REAL, maximum_drawdown REAL, status TEXT);
        """)
        now = datetime.now(timezone.utc)
        started = now - timedelta(seconds=12)
        result = {"stages": [{"stage": "NEWS_RESEARCH", "status": "SUCCEEDED", "detail": {"articles_fetched": 3, "signals_stored": 2, "provider": "TWELVE_DATA"}, "warnings": []}, {"stage": "SHADOW_ANALYSIS", "status": "SUCCEEDED", "detail": {"opportunities_seen": 2, "decisions_skipped": 0}, "warnings": []}, {"stage": "SHADOW_PERFORMANCE", "status": "SUCCEEDED", "detail": {"total_decisions": 2, "measured_1d_decisions": 2, "directional_success_percent": 50.0, "profitable_after_cost_percent": 50.0}, "warnings": []}]}
        connection.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("j1","INTELLIGENCE_CYCLE","SUCCEEDED",started.isoformat(),started.isoformat(),now.isoformat(),"{}",json.dumps(result),None,None,"k"))
        connection.execute("INSERT INTO run_history VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("r1","NEWS_RESEARCH","SUCCEEDED",started.isoformat(),now.isoformat(),"TWELVE_DATA","[]",2,8,0,None,None,"{}"))
        for did, symbol, confidence, sentiment, ret in [("d1","AAPL",0.85,"POSITIVE",0.03),("d2","XOM",0.92,"POSITIVE",-0.02)]:
            connection.execute("INSERT INTO shadow_decisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (did,"a",symbol,started.isoformat(),"v1","BLOCKED",90,confidence,sentiment,"EVENT",1,"Headline",0,"[]",json.dumps(["Platform trading-readiness checks have not passed."]),None,None))
            connection.execute("INSERT INTO decision_outcomes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f"o-{did}",did,symbol,1,now.date().isoformat(),now.isoformat(),100,100*(1+ret),ret,"SPY",100,101,0.01,ret-0.01,ret,max(-ret,0),"MEASURED"))
        connection.execute("INSERT INTO copilot_decision_snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("s1",now.isoformat(),"CURRENT","HEALTHY","NOT_READY","CAUTIOUS",0.89,10,2,"STRONG",0,2,8,6,"HOLD","[]"))
        connection.commit()


def test_generates_v2_analytics(tmp_path) -> None:
    database = tmp_path / "application.db"
    create_database(database)
    review = PerformanceReviewService(database_path=str(database)).generate(start=datetime.now(timezone.utc)-timedelta(days=1), end=datetime.now(timezone.utc)+timedelta(minutes=1))
    assert review["system_health"]["intelligence_cycles"] == 1
    assert review["confidence_calibration"]["calibration_sample_size"] == 2
    assert review["sector_analytics"]
    assert review["symbol_analytics"][0]["symbol"] in {"AAPL", "XOM"}
    assert review["blocker_analytics"]["total_blocker_events"] == 2
    assert review["trends"]
    assert review["maturity"]["score_percent"] > 0
    assert "Sector Leaders" in review["markdown"]


def test_handles_empty_database(tmp_path) -> None:
    database = tmp_path / "empty.db"
    with sqlite3.connect(database):
        pass
    review = PerformanceReviewService(database_path=str(database)).generate()
    assert review["sector_analytics"] == []
    assert review["symbol_analytics"] == []
    assert review["confidence_calibration"]["calibration_sample_size"] == 0
