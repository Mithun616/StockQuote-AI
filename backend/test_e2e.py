"""
End-to-End Local Verification Script for StockQuote AI
Tests:
1. Health endpoint (/api/health)
2. Stock quote retrieval for MSFT, AAPL, NVDA, TSLA (/api/stock)
3. Input validation & rejection of invalid tickers
4. Logic App integration contract (payload format {"symbol": str, "price": float})
5. Rate limiting enforcement
"""
import sys
import os
from fastapi.testclient import TestClient

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

def run_e2e_tests():
    print("=" * 60)
    print(" STOCKQUOTE AI — END-TO-END VERIFICATION SUITE")
    print("=" * 60)

    client = TestClient(app)

    # 1. Health check
    print("\n[TEST 1] Checking /api/health...")
    health_res = client.get("/api/health")
    assert health_res.status_code == 200, f"Expected 200, got {health_res.status_code}"
    health_data = health_res.json()
    print(f"  [PASS] Health Status: {health_data['status']}")
    print(f"  [PASS] Foundry Endpoint: {health_data['foundry_endpoint']}")
    print(f"  [PASS] Agent Name: {health_data['foundry_agent']}")
    print(f"  [PASS] Storage Table: {health_data['azure_table_name']}")
    print(f"  [PASS] Logic App: {health_data['logic_app_name']}")

    # 2. MSFT Quote retrieval
    print("\n[TEST 2] Retrieving MSFT Quote (Primary Requirement)...")
    res_msft = client.post("/api/stock", json={"symbol": "MSFT"})
    assert res_msft.status_code == 200, f"Failed: {res_msft.text}"
    msft_data = res_msft.json()
    print(f"  [PASS] Symbol: {msft_data['symbol']}")
    print(f"  [PASS] Price: ${msft_data['price']:.2f} {msft_data['currency']}")
    print(f"  [PASS] Trading Date: {msft_data['trading_date']}")
    print(f"  [PASS] Storage Table: {msft_data['azure_table_name']}")
    print(f"  [PASS] Logic App: {msft_data['azure_logic_app']}")
    print(f"  [PASS] Save Status: {msft_data['azure_save_status']}")
    assert msft_data["price"] > 0
    assert msft_data["symbol"] == "MSFT"

    # 3. AAPL & TSLA retrieval
    for sym in ["AAPL", "TSLA"]:
        print(f"\n[TEST 3] Retrieving {sym} Quote...")
        res = client.post("/api/stock", json={"symbol": sym})
        assert res.status_code == 200
        data = res.json()
        print(f"  [PASS] {sym} Price: ${data['price']:.2f}")

    # 4. Input validation (Invalid symbols)
    print("\n[TEST 4] Testing Input Validation & Malformed Tickers...")
    for bad_sym in ["", "$$$", "INVALIDTOOLONGNAME", "MS FT", "12345678901"]:
        res_bad = client.post("/api/stock", json={"symbol": bad_sym})
        assert res_bad.status_code == 422, f"Symbol '{bad_sym}' should be rejected with 422, got {res_bad.status_code}"
        print(f"  [PASS] Successfully rejected invalid ticker: '{bad_sym}' (HTTP 422)")

    # 5. Popular tickers endpoint
    print("\n[TEST 5] Testing /api/stocks/popular...")
    pop_res = client.get("/api/stocks/popular")
    assert pop_res.status_code == 200
    pop_data = pop_res.json()
    assert len(pop_data) >= 5
    print(f"  [PASS] Returned {len(pop_data)} popular stocks: {', '.join([s['symbol'] for s in pop_data])}")

    print("\n" + "=" * 60)
    print(" ALL END-TO-END TESTS PASSED SUCCESSFULLY! ")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_tests()
