from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional
from datetime import date
from decimal import Decimal
import os
import logging

from database import get_db, init_db
from models import SecurityType
from schemas import (
    SecurityCreate, SecurityUpdate, Security,
    PortfolioCreate, Portfolio, PortfolioSummary,
    HoldingCreate, HoldingUpdate, Holding, HoldingDetail,
    CouponPayment, YieldCurve, YieldCurveCreate,
    YieldCalculation, PortfolioValuation, PortfolioAnalytics,
    YTMCalculationRequest
)
from services import (
    SecurityService, PortfolioService, HoldingService,
    AnalyticsService, CouponService
)
from financial_calculator import FinancialCalculator

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize database on startup
try:
    init_db()
    logging.info("Database initialized successfully")
except Exception as e:
    logging.error(f"Database initialization failed: {e}")

# Create FastAPI app
app = FastAPI(
    title="Fixed-Income Portfolio API",
    description="RESTful API for managing fixed-income investments and calculating portfolio returns",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SECURITY ENDPOINTS
# ============================================================================

@api_router.post("/securities", response_model=Security, status_code=201)
async def create_security(
    security: SecurityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new fixed income security"""
    try:
        db_security = await SecurityService.create_security(db, security)
        return db_security
    except Exception as e:
        logger.error(f"Error creating security: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/securities", response_model=List[Security])
async def list_securities(
    security_type: Optional[SecurityType] = None,
    issuer: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List securities with optional filters"""
    securities = await SecurityService.list_securities(
        db, security_type=security_type, issuer=issuer, skip=skip, limit=limit
    )
    return securities

@api_router.get("/securities/{security_id}", response_model=Security)
async def get_security(
    security_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get security by ID"""
    security = await SecurityService.get_security(db, security_id)
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    return security

@api_router.put("/securities/{security_id}", response_model=Security)
async def update_security(
    security_id: str,
    security_update: SecurityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update security details"""
    security = await SecurityService.update_security(db, security_id, security_update)
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    return security

@api_router.delete("/securities/{security_id}", status_code=204)
async def delete_security(
    security_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a security"""
    success = await SecurityService.delete_security(db, security_id)
    if not success:
        raise HTTPException(status_code=404, detail="Security not found")
    return None

# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@api_router.post("/portfolios", response_model=Portfolio, status_code=201)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new portfolio"""
    try:
        db_portfolio = await PortfolioService.create_portfolio(db, portfolio)
        return db_portfolio
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/portfolios", response_model=List[Portfolio])
async def list_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List all portfolios"""
    portfolios = await PortfolioService.list_portfolios(db, skip=skip, limit=limit)
    return portfolios

@api_router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio by ID"""
    portfolio = await PortfolioService.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@api_router.delete("/portfolios/{portfolio_id}", status_code=204)
async def delete_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a portfolio"""
    success = await PortfolioService.delete_portfolio(db, portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return None

# ============================================================================
# HOLDINGS ENDPOINTS
# ============================================================================

@api_router.post("/portfolios/{portfolio_id}/holdings", response_model=Holding, status_code=201)
async def create_holding(
    portfolio_id: str,
    holding: HoldingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a holding to a portfolio"""
    db_holding = await HoldingService.create_holding(db, portfolio_id, holding)
    if not db_holding:
        raise HTTPException(status_code=404, detail="Portfolio or Security not found")
    return db_holding

@api_router.get("/portfolios/{portfolio_id}/holdings", response_model=List[Holding])
async def list_holdings(
    portfolio_id: str,
    current_only: bool = Query(True, description="Show only current holdings"),
    db: AsyncSession = Depends(get_db)
):
    """List all holdings in a portfolio"""
    holdings = await HoldingService.list_holdings(db, portfolio_id, current_only=current_only)
    return holdings

@api_router.get("/holdings/{holding_id}", response_model=Holding)
async def get_holding(
    holding_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get holding by ID"""
    holding = await HoldingService.get_holding(db, holding_id)
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding

@api_router.put("/holdings/{holding_id}", response_model=Holding)
async def update_holding(
    holding_id: str,
    holding_update: HoldingUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update holding details"""
    holding = await HoldingService.update_holding(db, holding_id, holding_update)
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding

@api_router.delete("/holdings/{holding_id}", status_code=204)
async def delete_holding(
    holding_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a holding (soft delete)"""
    success = await HoldingService.delete_holding(db, holding_id)
    if not success:
        raise HTTPException(status_code=404, detail="Holding not found")
    return None

@api_router.get("/holdings/{holding_id}/schedule", response_model=List[CouponPayment])
async def get_coupon_schedule(
    holding_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get coupon payment schedule for a holding"""
    schedule = await CouponService.generate_coupon_schedule(db, holding_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Holding not found or unable to generate schedule")
    return schedule

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@api_router.get("/holdings/{holding_id}/yields", response_model=YieldCalculation)
async def calculate_holding_yields(
    holding_id: str,
    current_price: Optional[Decimal] = Query(None, description="Current market price as % of face value"),
    db: AsyncSession = Depends(get_db)
):
    """Calculate yield metrics for a holding"""
    yields = await AnalyticsService.calculate_holding_yields(db, holding_id, current_price)
    if not yields:
        raise HTTPException(status_code=404, detail="Holding not found")
    return yields

@api_router.get("/portfolios/{portfolio_id}/valuation", response_model=PortfolioValuation)
async def get_portfolio_valuation(
    portfolio_id: str,
    as_of_date: Optional[date] = Query(None, description="Valuation date (defaults to today)"),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio valuation"""
    valuation = await AnalyticsService.calculate_portfolio_valuation(db, portfolio_id, as_of_date)
    if not valuation:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return valuation

@api_router.get("/portfolios/{portfolio_id}/analytics", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio analytics including yield, duration, and convexity"""
    analytics = await AnalyticsService.calculate_portfolio_analytics(db, portfolio_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return analytics

@api_router.post("/calculate/ytm", response_model=dict)
async def calculate_ytm(request: YTMCalculationRequest):
    """Calculate Yield to Maturity for custom parameters"""
    ytm = FinancialCalculator.calculate_ytm(
        face_value=request.face_value,
        coupon_rate=request.coupon_rate,
        frequency=request.coupon_frequency,
        years_to_maturity=request.years_to_maturity,
        current_price=request.current_price
    )
    
    if ytm is None:
        raise HTTPException(status_code=400, detail="Unable to calculate YTM. Check input parameters.")
    
    return {
        "ytm": float(ytm),
        "ytm_percentage": f"{float(ytm):.2f}%"
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fixed-Income Portfolio API",
        "version": "1.0.0"
    }

# Include router in app
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "message": "Fixed-Income Portfolio & Return Calculator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }
