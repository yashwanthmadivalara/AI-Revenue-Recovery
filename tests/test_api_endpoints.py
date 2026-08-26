import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_simulator_scenarios():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/simulator/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert "soft_decline" in scenarios
        assert "abandoned_checkout" in scenarios

        # Run soft_decline scenario
        run_res = await ac.post("/api/v1/simulator/run/soft_decline")
        assert run_res.status_code == 200
        data = run_res.json()
        assert data["scenario"] == "soft_decline"
        assert data["status"] == "resolved"


@pytest.mark.asyncio
async def test_guardrail_config_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/guardrails/config")
        assert response.status_code == 200
        config = response.json()
        assert config["max_contact_attempts_per_week"] >= 1
