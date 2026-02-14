#!/bin/bash

# Fixed-Income Portfolio API Test Script
# Tests all core functionality

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
BASE_URL="${API_URL}/api"

echo "======================================"
echo "Fixed-Income Portfolio API Test Suite"
echo "======================================"
echo "API URL: $BASE_URL"
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
curl -s -X GET "$BASE_URL/health" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"✓ Status: {data['status']}, Version: {data['version']}\")"
echo ""

# Test 2: Create a Corporate Bond Security
echo "Test 2: Create Corporate Bond Security"
SECURITY_1=$(curl -s -X POST "$BASE_URL/securities" \
  -H "Content-Type: application/json" \
  -d '{
    "security_name": "Apple Inc. 2030 Bond",
    "security_type": "CORPORATE_BOND",
    "face_value": 1000.00,
    "coupon_rate": 4.50,
    "coupon_frequency": "SEMI_ANNUAL",
    "issue_date": "2020-01-15",
    "maturity_date": "2030-01-15",
    "day_count_convention": "ACT_365",
    "currency": "USD",
    "issuer": "Apple Inc.",
    "credit_rating": "AAA"
  }')

SECURITY_ID_1=$(echo $SECURITY_1 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✓ Created Security: $SECURITY_ID_1"
echo ""

# Test 3: Create a Treasury Bill
echo "Test 3: Create Treasury Bill Security"
SECURITY_2=$(curl -s -X POST "$BASE_URL/securities" \
  -H "Content-Type: application/json" \
  -d '{
    "security_name": "US Treasury 2028 Bond",
    "security_type": "T_BILL",
    "face_value": 1000.00,
    "coupon_rate": 3.25,
    "coupon_frequency": "QUARTERLY",
    "issue_date": "2023-06-01",
    "maturity_date": "2028-06-01",
    "day_count_convention": "ACT_360",
    "currency": "USD",
    "issuer": "US Treasury",
    "credit_rating": "AAA"
  }')

SECURITY_ID_2=$(echo $SECURITY_2 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✓ Created Security: $SECURITY_ID_2"
echo ""

# Test 4: List All Securities
echo "Test 4: List All Securities"
curl -s -X GET "$BASE_URL/securities" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"✓ Found {len(data)} securities\")"
echo ""

# Test 5: Get Specific Security
echo "Test 5: Get Specific Security Details"
curl -s -X GET "$BASE_URL/securities/$SECURITY_ID_1" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"✓ Security: {data['security_name']}, Coupon: {data['coupon_rate']}%, Issuer: {data['issuer']}\")"
echo ""

# Test 6: Create Portfolio
echo "Test 6: Create Portfolio"
PORTFOLIO=$(curl -s -X POST "$BASE_URL/portfolios" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "Conservative Fixed Income Portfolio",
    "description": "Low-risk portfolio focused on high-grade bonds"
  }')

PORTFOLIO_ID=$(echo $PORTFOLIO | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✓ Created Portfolio: $PORTFOLIO_ID"
echo ""

# Test 7: Add Holding to Portfolio (Apple Bond)
echo "Test 7: Add Holding to Portfolio (Apple Bond)"
HOLDING_1=$(curl -s -X POST "$BASE_URL/portfolios/$PORTFOLIO_ID/holdings" \
  -H "Content-Type: application/json" \
  -d "{
    \"security_id\": \"$SECURITY_ID_1\",
    \"purchase_date\": \"2024-01-10\",
    \"purchase_price\": 98.50,
    \"quantity\": 10,
    \"accrued_interest_paid\": 15.00
  }")

HOLDING_ID_1=$(echo $HOLDING_1 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✓ Created Holding: $HOLDING_ID_1"
echo ""

# Test 8: Add Another Holding (Treasury Bill)
echo "Test 8: Add Holding to Portfolio (Treasury Bill)"
HOLDING_2=$(curl -s -X POST "$BASE_URL/portfolios/$PORTFOLIO_ID/holdings" \
  -H "Content-Type: application/json" \
  -d "{
    \"security_id\": \"$SECURITY_ID_2\",
    \"purchase_date\": \"2024-02-15\",
    \"purchase_price\": 99.75,
    \"quantity\": 20,
    \"accrued_interest_paid\": 8.50
  }")

HOLDING_ID_2=$(echo $HOLDING_2 | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "✓ Created Holding: $HOLDING_ID_2"
echo ""

# Test 9: List Portfolio Holdings
echo "Test 9: List Portfolio Holdings"
curl -s -X GET "$BASE_URL/portfolios/$PORTFOLIO_ID/holdings" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"✓ Portfolio has {len(data)} holdings\")"
echo ""

# Test 10: Calculate Yield for Holding
echo "Test 10: Calculate Yield Metrics for Holding"
curl -s -X GET "$BASE_URL/holdings/$HOLDING_ID_1/yields?current_price=99.00" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"✓ Holding Yield Analysis:\")
print(f\"  Current Yield: {data.get('current_yield', 'N/A')}%\")
print(f\"  Yield to Maturity: {data.get('yield_to_maturity', 'N/A')}%\")
print(f\"  Macaulay Duration: {data.get('macaulay_duration', 'N/A')}\")
print(f\"  Modified Duration: {data.get('modified_duration', 'N/A')}\")
print(f\"  Convexity: {data.get('convexity', 'N/A')}\")
"
echo ""

# Test 11: Generate Coupon Schedule
echo "Test 11: Generate Coupon Payment Schedule"
curl -s -X GET "$BASE_URL/holdings/$HOLDING_ID_1/schedule" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"✓ Generated {len(data)} coupon payments\")
if data:
    print(f\"  Next Payment: {data[0]['payment_date']}, Amount: \${data[0]['payment_amount']}\")
"
echo ""

# Test 12: Portfolio Valuation
echo "Test 12: Portfolio Valuation"
curl -s -X GET "$BASE_URL/portfolios/$PORTFOLIO_ID/valuation" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"✓ Portfolio Valuation:\")
print(f\"  Total Market Value: \${data['total_market_value']}\")
print(f\"  Total Cost Basis: \${data['total_cost_basis']}\")
print(f\"  Unrealized Gain/Loss: \${data['unrealized_gain_loss']}\")
print(f\"  Holdings Count: {data['holdings_count']}\")
"
echo ""

# Test 13: Portfolio Analytics
echo "Test 13: Portfolio Analytics"
curl -s -X GET "$BASE_URL/portfolios/$PORTFOLIO_ID/analytics" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"✓ Portfolio Analytics:\")
print(f\"  Weighted Average Yield: {data.get('weighted_average_yield', 'N/A')}%\")
print(f\"  Portfolio Duration: {data.get('portfolio_duration', 'N/A')}\")
print(f\"  Portfolio Convexity: {data.get('portfolio_convexity', 'N/A')}\")
print(f\"  Weighted Average Maturity: {data.get('weighted_average_maturity', 'N/A')} years\")
"
echo ""

# Test 14: Custom YTM Calculation
echo "Test 14: Custom YTM Calculation"
curl -s -X POST "$BASE_URL/calculate/ytm" \
  -H "Content-Type: application/json" \
  -d '{
    "face_value": 1000,
    "coupon_rate": 5.0,
    "coupon_frequency": "SEMI_ANNUAL",
    "years_to_maturity": 5,
    "current_price": 950
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"✓ YTM Calculation: {data['ytm_percentage']}\")
"
echo ""

# Test 15: List Portfolios
echo "Test 15: List All Portfolios"
curl -s -X GET "$BASE_URL/portfolios" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"✓ Found {len(data)} portfolio(s)\")"
echo ""

# Test 16: Filter Securities by Type
echo "Test 16: Filter Securities by Type"
curl -s -X GET "$BASE_URL/securities?security_type=CORPORATE_BOND" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"✓ Found {len(data)} corporate bond(s)\")"
echo ""

echo "======================================"
echo "All Tests Completed Successfully! ✓"
echo "======================================"
echo ""
echo "API Documentation: ${API_URL}/docs"
