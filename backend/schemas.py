from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from models import SecurityType, CouponFrequency, DayCountConvention, PaymentStatus

# Security Schemas
class SecurityBase(BaseModel):
    security_name: str
    security_type: SecurityType
    face_value: Decimal = Field(ge=0)
    coupon_rate: Decimal = Field(ge=0, le=100)
    coupon_frequency: CouponFrequency
    issue_date: date
    maturity_date: date
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365
    currency: str = "USD"
    issuer: str
    credit_rating: Optional[str] = None

class SecurityCreate(SecurityBase):
    pass

class SecurityUpdate(BaseModel):
    security_name: Optional[str] = None
    coupon_rate: Optional[Decimal] = None
    credit_rating: Optional[str] = None

class Security(SecurityBase):
    model_config = ConfigDict(from_attributes=True)
    id: str

# Portfolio Schemas
class PortfolioBase(BaseModel):
    portfolio_name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class Portfolio(PortfolioBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_date: datetime
    last_modified: datetime
    total_invested: Decimal

class PortfolioSummary(Portfolio):
    holdings_count: int = 0
    current_value: Optional[Decimal] = None

# Holding Schemas
class HoldingBase(BaseModel):
    security_id: str
    purchase_date: date
    purchase_price: Decimal = Field(ge=0)
    quantity: Decimal = Field(gt=0)
    accrued_interest_paid: Decimal = Field(default=Decimal("0.0"), ge=0)

class HoldingCreate(HoldingBase):
    pass

class HoldingUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    current_holding: Optional[bool] = None

class Holding(HoldingBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    portfolio_id: str
    current_holding: bool

class HoldingDetail(Holding):
    security: Security

# Coupon Payment Schemas
class CouponPaymentBase(BaseModel):
    payment_date: date
    payment_amount: Decimal
    accrued_days: int = 0
    status: PaymentStatus = PaymentStatus.PROJECTED

class CouponPayment(CouponPaymentBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    holding_id: str

# Yield Curve Schemas
class YieldCurveBase(BaseModel):
    curve_name: str
    curve_date: date
    tenor: str
    yield_rate: Decimal

class YieldCurveCreate(YieldCurveBase):
    pass

class YieldCurve(YieldCurveBase):
    model_config = ConfigDict(from_attributes=True)
    id: str

# Analytics Response Schemas
class YieldCalculation(BaseModel):
    holding_id: str
    current_yield: Optional[Decimal] = None
    yield_to_maturity: Optional[Decimal] = None
    macaulay_duration: Optional[Decimal] = None
    modified_duration: Optional[Decimal] = None
    convexity: Optional[Decimal] = None

class PortfolioValuation(BaseModel):
    portfolio_id: str
    as_of_date: date
    total_market_value: Decimal
    total_cost_basis: Decimal
    unrealized_gain_loss: Decimal
    holdings_count: int

class PortfolioAnalytics(BaseModel):
    portfolio_id: str
    weighted_average_yield: Optional[Decimal] = None
    portfolio_duration: Optional[Decimal] = None
    portfolio_convexity: Optional[Decimal] = None
    weighted_average_maturity: Optional[Decimal] = None

class PortfolioReturns(BaseModel):
    portfolio_id: str
    start_date: date
    end_date: date
    total_return: Decimal
    income_return: Decimal
    price_return: Decimal
    time_weighted_return: Optional[Decimal] = None

class YTMCalculationRequest(BaseModel):
    face_value: Decimal = Field(gt=0)
    coupon_rate: Decimal = Field(ge=0, le=100)
    coupon_frequency: CouponFrequency
    years_to_maturity: Decimal = Field(gt=0)
    current_price: Decimal = Field(gt=0)
