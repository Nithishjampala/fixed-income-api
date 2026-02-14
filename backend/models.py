from sqlalchemy import Column, String, Numeric, Date, DateTime, Enum, Integer, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid

class SecurityType(str, enum.Enum):
    GOVERNMENT_BOND = "GOVERNMENT_BOND"
    CORPORATE_BOND = "CORPORATE_BOND"
    T_BILL = "T_BILL"
    CD = "CD"
    DEBENTURE = "DEBENTURE"

class CouponFrequency(str, enum.Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"
    ZERO_COUPON = "ZERO_COUPON"

class DayCountConvention(str, enum.Enum):
    ACT_360 = "ACT_360"
    ACT_365 = "ACT_365"
    THIRTY_360 = "THIRTY_360"
    ACT_ACT = "ACT_ACT"

class PaymentStatus(str, enum.Enum):
    PROJECTED = "PROJECTED"
    PAID = "PAID"
    MISSED = "MISSED"

class FixedIncomeSecurity(Base):
    __tablename__ = "fixed_income_securities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    security_name = Column(String(255), nullable=False)
    security_type = Column(Enum(SecurityType), nullable=False)
    face_value = Column(Numeric(15, 2), nullable=False)
    coupon_rate = Column(Numeric(5, 2), nullable=False)  # Annual percentage
    coupon_frequency = Column(Enum(CouponFrequency), nullable=False)
    issue_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    day_count_convention = Column(Enum(DayCountConvention), nullable=False, default=DayCountConvention.ACT_365)
    currency = Column(String(3), default="USD")
    issuer = Column(String(255), nullable=False)
    credit_rating = Column(String(10), nullable=True)
    
    # Relationships
    holdings = relationship("PortfolioHolding", back_populates="security")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_date = Column(DateTime, server_default=func.now())
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())
    total_invested = Column(Numeric(15, 2), default=0.0)
    
    # Relationships
    holdings = relationship("PortfolioHolding", back_populates="portfolio")

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False)
    security_id = Column(String(36), ForeignKey("fixed_income_securities.id"), nullable=False)
    purchase_date = Column(Date, nullable=False)
    purchase_price = Column(Numeric(15, 4), nullable=False)  # As percentage of face value
    quantity = Column(Numeric(15, 4), nullable=False)  # Number of bonds/units
    accrued_interest_paid = Column(Numeric(15, 4), default=0.0)
    current_holding = Column(Boolean, default=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    security = relationship("FixedIncomeSecurity", back_populates="holdings")
    coupon_payments = relationship("CouponPayment", back_populates="holding")

class CouponPayment(Base):
    __tablename__ = "coupon_payments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    holding_id = Column(String(36), ForeignKey("portfolio_holdings.id"), nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Numeric(15, 4), nullable=False)
    accrued_days = Column(Integer, default=0)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PROJECTED)
    
    # Relationships
    holding = relationship("PortfolioHolding", back_populates="coupon_payments")

class YieldCurve(Base):
    __tablename__ = "yield_curves"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    curve_name = Column(String(100), nullable=False)
    curve_date = Column(Date, nullable=False)
    tenor = Column(String(10), nullable=False)  # e.g., "1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y"
    yield_rate = Column(Numeric(8, 4), nullable=False)
    
    __table_args__ = (UniqueConstraint('curve_date', 'tenor', name='_curve_date_tenor_uc'),)
