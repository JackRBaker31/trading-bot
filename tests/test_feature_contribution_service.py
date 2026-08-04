import json
import sqlite3
from pathlib import Path

from app.feature_contribution_service import FeatureContributionService


def test_generates_feature_analytics_from_snapshots_and_outcomes(tmp_path: Path) -> None:
    database = tmp_path / "application.db"
    with sqlite3.connect(database) as connection:
        connection.execute("""
            CREATE TABLE opportunity_ranking_snapshots (
                snapshot_id INTEGER PRIMARY KEY, captured_at TEXT, symbol TEXT,
                rank INTEGER, opportunity_score REAL,
                component_values_json TEXT, component_labels_json TEXT
            )
        """)
        connection.execute("""
            CREATE TABLE opportunity_ranking_forward_outcomes (
                outcome_id INTEGER PRIMARY KEY, snapshot_id INTEGER,
                horizon_days INTEGER, return_percent REAL,
                alpha_percent REAL, maximum_drawdown_percent REAL
            )
        """)
        for snapshot_id, ret, alpha in [(1, 2.0, 1.0), (2, -1.0, -1.5), (3, 3.0, 2.0)]:
            connection.execute(
                "INSERT INTO opportunity_ranking_snapshots VALUES (?, '2099-01-01T00:00:00+00:00', ?, ?, ?, ?, ?)",
                (snapshot_id, f"S{snapshot_id}", snapshot_id, 80.0,
                 json.dumps({"NEWS": 10.0 + snapshot_id, "RISK": 2.0}),
                 json.dumps({"NEWS": "News", "RISK": "Risk"})),
            )
            connection.execute(
                "INSERT INTO opportunity_ranking_forward_outcomes VALUES (?, ?, 1, ?, ?, 0.5)",
                (snapshot_id, snapshot_id, ret, alpha),
            )
    report = FeatureContributionService(database_path=str(database)).generate(days=365, horizon_days=1)
    assert report["trading_impact"] == "NONE"
    assert report["summary"]["measured_outcome_count"] == 3
    assert report["features"][0]["label"] == "News"
    assert report["latest_vectors"][0]["components"]
