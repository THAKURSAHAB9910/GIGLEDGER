"""Tests for GIGLEDGER FastAPI endpoints and analytical services."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["total_shifts_in_db"] > 0
    assert data["currency"] == "INR"


def test_api_metrics_summary():
    res = client.get("/api/metrics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_shifts"] > 0
    assert data["total_gross_earnings"] > 0
    assert data["total_net_earnings"] > 0
    assert data["effective_hourly_net"] > 0
    assert "sub_minimum_wage_shift_count" in data


def test_api_payout_reconciliation():
    res = client.get("/api/analytics/reconciliation?limit=20")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 20
    assert "gross_advertised_payout" in items[0]
    assert "net_bank_settlement" in items[0]
    assert "take_home_retention_pct" in items[0]
    assert "reconciliation_status" in items[0]


def test_api_shift_profitability():
    res = client.get("/api/analytics/shift-profitability")
    assert res.status_code == 200
    data = res.json()
    assert data["profitable_shifts_count"] > 0
    assert "profit_margin_tiers" in data
    assert "avg_break_even_deliveries" in data
    assert data["avg_break_even_deliveries"] > 0


def test_api_shifts_pagination():
    res = client.get("/api/shifts?limit=25&offset=10")
    assert res.status_code == 200
    data = res.json()
    assert data["limit"] == 25
    assert data["offset"] == 10
    assert len(data["records"]) == 25


def test_api_benchmarks():
    res = client.get("/api/analytics/benchmarks")
    assert res.status_code == 200
    benchmarks = res.json()
    assert len(benchmarks) > 0
    assert any("Fairwork" in b["source_title"] for b in benchmarks)
