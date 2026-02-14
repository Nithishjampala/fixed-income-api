# Fixed-Income Portfolio & Return Calculator API

A comprehensive RESTful API built with FastAPI and MySQL for managing fixed-income investments and calculating portfolio returns. This API supports various fixed-income instruments including bonds, treasury bills, certificates of deposit (CDs), and debentures with advanced yield calculations.

## Features

### Core Functionality
- ✅ **CRUD Operations**: Complete management of securities, portfolios, and holdings
- ✅ **Yield Calculations**: 
  - Current Yield
  - Yield to Maturity (YTM) using Newton-Raphson method
  - Macaulay Duration
  - Modified Duration
  - Convexity
- ✅ **Portfolio Analytics**:
  - Portfolio valuation
  - Weighted average yield
  - Portfolio duration and convexity
  - Weighted average maturity
- ✅ **Coupon Schedule Generation**: Automatic generation of payment schedules

### Supported Securities
- Government Bonds
- Corporate Bonds
- Treasury Bills (T-Bills)
- Certificates of Deposit (CDs)
- Debentures

### Day Count Conventions
- ACT/360
- ACT/365
- 30/360
- ACT/ACT

### Coupon Frequencies
- Monthly
- Quarterly
- Semi-Annual
- Annual
- Zero Coupon

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: MySQL 8.0 (MariaDB)
- **ORM**: SQLAlchemy with async support (aiomysql)
- **Validation**: Pydantic v2
- **Financial Calculations**: NumPy
- **API Documentation**: OpenAPI/Swagger (auto-generated)

## Database Schema

### Tables

1. **fixed_income_securities**
   - Stores bond and security information
   - Fields: id, security_name, security_type, face_value, coupon_rate, etc.

2. **portfolios**
   - Portfolio metadata
   - Fields: id, portfolio_name, description, created_date, total_invested

3. **portfolio_holdings**
   - Links securities to portfolios
   - Fields: id, portfolio_id, security_id, purchase_date, quantity, etc.

4. **coupon_payments**
   - Tracks coupon payment schedule
   - Fields: id, holding_id, payment_date, payment_amount, status

5. **yield_curves**
   - Historical yield curve data
   - Fields: id, curve_name, curve_date, tenor, yield_rate

## API Endpoints

### Health Check
- `GET /api/health` - Health check endpoint

### Securities Management
- `POST /api/securities` - Create a new security
- `GET /api/securities` - List all securities (with filters)
- `GET /api/securities/{security_id}` - Get security details
- `PUT /api/securities/{security_id}` - Update security
- `DELETE /api/securities/{security_id}` - Delete security

### Portfolio Management
- `POST /api/portfolios` - Create a new portfolio
- `GET /api/portfolios` - List all portfolios
- `GET /api/portfolios/{portfolio_id}` - Get portfolio details
- `DELETE /api/portfolios/{portfolio_id}` - Delete portfolio

### Holdings Management
- `POST /api/portfolios/{portfolio_id}/holdings` - Add holding to portfolio
- `GET /api/portfolios/{portfolio_id}/holdings` - List portfolio holdings
- `GET /api/holdings/{holding_id}` - Get holding details
- `PUT /api/holdings/{holding_id}` - Update holding
- `DELETE /api/holdings/{holding_id}` - Remove holding (soft delete)
- `GET /api/holdings/{holding_id}/schedule` - Get coupon payment schedule

### Analytics
- `GET /api/holdings/{holding_id}/yields` - Calculate yield metrics for a holding
- `GET /api/portfolios/{portfolio_id}/valuation` - Get portfolio valuation
- `GET /api/portfolios/{portfolio_id}/analytics` - Get portfolio analytics
- `POST /api/calculate/ytm` - Calculate YTM for custom parameters

## Installation & Setup

### Prerequisites
```bash
# Python 3.11+
python3 --version

# MySQL/MariaDB
mysql --version
```

### Install Dependencies
```bash
cd /app/backend
pip install -r requirements.txt
```

### Environment Configuration
Create/update `.env` file in `/app/backend/`:
```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=fixed_income_db
CORS_ORIGINS=*
```

### Database Setup
The application automatically creates the database and tables on startup.

### Start the Server
```bash
# Using supervisor (production)
sudo supervisorctl restart backend

# Or directly (development)
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

## Usage Examples

### 1. Create a Corporate Bond
```bash
curl -X POST "http://localhost:8001/api/securities" \
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
  }'
```

### 2. Create a Portfolio
```bash
curl -X POST "http://localhost:8001/api/portfolios" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "Conservative Fixed Income",
    "description": "Low-risk bond portfolio"
  }'
```

### 3. Add Holding to Portfolio
```bash
curl -X POST "http://localhost:8001/api/portfolios/{portfolio_id}/holdings" \
  -H "Content-Type: application/json" \
  -d '{
    "security_id": "{security_id}",
    "purchase_date": "2024-01-10",
    "purchase_price": 98.50,
    "quantity": 10,
    "accrued_interest_paid": 15.00
  }'
```

### 4. Calculate Yield Metrics
```bash
curl -X GET "http://localhost:8001/api/holdings/{holding_id}/yields?current_price=99.00"
```

Response:
```json
{
  "holding_id": "abc123",
  "current_yield": 4.55,
  "yield_to_maturity": 4.34,
  "macaulay_duration": 3.63,
  "modified_duration": 3.55,
  "convexity": 14.97
}
```

### 5. Get Portfolio Analytics
```bash
curl -X GET "http://localhost:8001/api/portfolios/{portfolio_id}/analytics"
```

Response:
```json
{
  "portfolio_id": "xyz789",
  "weighted_average_yield": 3.69,
  "portfolio_duration": 2.65,
  "portfolio_convexity": 8.64,
  "weighted_average_maturity": 2.84
}
```

### 6. Calculate Custom YTM
```bash
curl -X POST "http://localhost:8001/api/calculate/ytm" \
  -H "Content-Type: application/json" \
  -d '{
    "face_value": 1000,
    "coupon_rate": 5.0,
    "coupon_frequency": "SEMI_ANNUAL",
    "years_to_maturity": 5,
    "current_price": 950
  }'
```

## Financial Calculations

### Yield to Maturity (YTM)
YTM is calculated using the Newton-Raphson iterative method:
- Solves for the discount rate that equates present value of all future cash flows to current price
- Handles all coupon frequencies including zero-coupon bonds
- Converges within 100 iterations with 0.01% tolerance

### Duration
- **Macaulay Duration**: Weighted average time to receive cash flows
- **Modified Duration**: Price sensitivity to yield changes
- Formula: Modified Duration = Macaulay Duration / (1 + YTM/n)

### Convexity
Measures the curvature of price-yield relationship:
- Higher convexity = better price performance when yields change
- Important for portfolio immunization strategies

### Coupon Schedule
- Automatically generates payment dates based on frequency
- Calculates accrued interest using specified day count convention
- Supports all standard payment frequencies

## Testing

Run the comprehensive test suite:
```bash
chmod +x /app/test_api.sh
/app/test_api.sh
```

The test suite covers:
- ✅ Health check
- ✅ Security CRUD operations
- ✅ Portfolio management
- ✅ Holdings management
- ✅ Yield calculations
- ✅ Coupon schedule generation
- ✅ Portfolio valuation
- ✅ Portfolio analytics
- ✅ Custom YTM calculation

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`
- **OpenAPI JSON**: `http://localhost:8001/openapi.json`

## Architecture

### Service Layer Pattern
- **SecurityService**: Manages security CRUD operations
- **PortfolioService**: Handles portfolio management
- **HoldingService**: Manages portfolio holdings
- **AnalyticsService**: Performs yield and return calculations
- **CouponService**: Generates payment schedules

### Financial Calculator
Standalone module for all financial calculations:
- Yield calculations (current yield, YTM)
- Duration and convexity
- Day count conventions
- Coupon date generation
- Accrued interest calculation

## Performance Considerations

- **Async/Await**: All database operations use async SQLAlchemy
- **Connection Pooling**: Managed by aiomysql
- **Pagination**: List endpoints support skip/limit parameters
- **Indexes**: Primary keys and foreign keys automatically indexed
- **Lazy Loading**: Relationships use LAZY fetch strategy

## Error Handling

The API returns standard HTTP status codes:
- `200 OK`: Successful GET/PUT requests
- `201 Created`: Successful POST requests
- `204 No Content`: Successful DELETE requests
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error with details

## Future Enhancements

- [ ] Scenario analysis (interest rate sensitivity)
- [ ] Portfolio returns calculation (time-weighted, IRR)
- [ ] Export to CSV/Excel
- [ ] Batch upload via CSV
- [ ] Yield curve management
- [ ] Reinvestment rate assumptions
- [ ] Authentication and authorization
- [ ] Multi-user support

## License

MIT License

## Contact

For questions or support, please contact the development team.

---

**Built with FastAPI and MySQL for robust fixed-income portfolio management.**
