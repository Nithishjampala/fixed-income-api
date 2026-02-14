from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from models import (
    FixedIncomeSecurity, Portfolio, PortfolioHolding, 
    CouponPayment, YieldCurve, SecurityType, PaymentStatus
)
from schemas import (
    SecurityCreate, SecurityUpdate,
    PortfolioCreate, HoldingCreate, HoldingUpdate,
    YieldCalculation, PortfolioValuation, PortfolioAnalytics,
    PortfolioReturns, CouponPayment as CouponPaymentSchema
)
from financial_calculator import FinancialCalculator

class SecurityService:
    """Service for managing fixed income securities"""
    
    @staticmethod
    async def create_security(db: AsyncSession, security: SecurityCreate) -> FixedIncomeSecurity:
        db_security = FixedIncomeSecurity(**security.model_dump())
        db.add(db_security)
        await db.commit()
        await db.refresh(db_security)
        return db_security
    
    @staticmethod
    async def get_security(db: AsyncSession, security_id: str) -> Optional[FixedIncomeSecurity]:
        result = await db.execute(select(FixedIncomeSecurity).filter(FixedIncomeSecurity.id == security_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_securities(
        db: AsyncSession,
        security_type: Optional[SecurityType] = None,
        issuer: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[FixedIncomeSecurity]:
        query = select(FixedIncomeSecurity)
        
        if security_type:
            query = query.filter(FixedIncomeSecurity.security_type == security_type)
        if issuer:
            query = query.filter(FixedIncomeSecurity.issuer.like(f"%{issuer}%"))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_security(
        db: AsyncSession, 
        security_id: str, 
        security_update: SecurityUpdate
    ) -> Optional[FixedIncomeSecurity]:
        db_security = await SecurityService.get_security(db, security_id)
        if not db_security:
            return None
        
        update_data = security_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_security, field, value)
        
        await db.commit()
        await db.refresh(db_security)
        return db_security
    
    @staticmethod
    async def delete_security(db: AsyncSession, security_id: str) -> bool:
        db_security = await SecurityService.get_security(db, security_id)
        if not db_security:
            return False
        
        await db.delete(db_security)
        await db.commit()
        return True

class PortfolioService:
    """Service for managing portfolios"""
    
    @staticmethod
    async def create_portfolio(db: AsyncSession, portfolio: PortfolioCreate) -> Portfolio:
        db_portfolio = Portfolio(**portfolio.model_dump())
        db.add(db_portfolio)
        await db.commit()
        await db.refresh(db_portfolio)
        return db_portfolio
    
    @staticmethod
    async def get_portfolio(db: AsyncSession, portfolio_id: str) -> Optional[Portfolio]:
        result = await db.execute(select(Portfolio).filter(Portfolio.id == portfolio_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_portfolios(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        result = await db.execute(select(Portfolio).offset(skip).limit(limit))
        return result.scalars().all()
    
    @staticmethod
    async def delete_portfolio(db: AsyncSession, portfolio_id: str) -> bool:
        db_portfolio = await PortfolioService.get_portfolio(db, portfolio_id)
        if not db_portfolio:
            return False
        
        await db.delete(db_portfolio)
        await db.commit()
        return True

class HoldingService:
    """Service for managing portfolio holdings"""
    
    @staticmethod
    async def create_holding(
        db: AsyncSession, 
        portfolio_id: str, 
        holding: HoldingCreate
    ) -> Optional[PortfolioHolding]:
        # Verify portfolio and security exist
        portfolio = await PortfolioService.get_portfolio(db, portfolio_id)
        security = await SecurityService.get_security(db, holding.security_id)
        
        if not portfolio or not security:
            return None
        
        db_holding = PortfolioHolding(
            portfolio_id=portfolio_id,
            **holding.model_dump()
        )
        db.add(db_holding)
        
        # Update portfolio total invested
        investment = float(holding.purchase_price) * float(holding.quantity) * float(security.face_value) / 100
        portfolio.total_invested = float(portfolio.total_invested) + investment
        
        await db.commit()
        await db.refresh(db_holding)
        return db_holding
    
    @staticmethod
    async def get_holding(db: AsyncSession, holding_id: str) -> Optional[PortfolioHolding]:
        result = await db.execute(
            select(PortfolioHolding)
            .filter(PortfolioHolding.id == holding_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_holdings(
        db: AsyncSession, 
        portfolio_id: str,
        current_only: bool = True
    ) -> List[PortfolioHolding]:
        query = select(PortfolioHolding).filter(PortfolioHolding.portfolio_id == portfolio_id)
        
        if current_only:
            query = query.filter(PortfolioHolding.current_holding == True)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_holding(
        db: AsyncSession,
        holding_id: str,
        holding_update: HoldingUpdate
    ) -> Optional[PortfolioHolding]:
        db_holding = await HoldingService.get_holding(db, holding_id)
        if not db_holding:
            return None
        
        update_data = holding_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_holding, field, value)
        
        await db.commit()
        await db.refresh(db_holding)
        return db_holding
    
    @staticmethod
    async def delete_holding(db: AsyncSession, holding_id: str) -> bool:
        """Soft delete holding"""
        db_holding = await HoldingService.get_holding(db, holding_id)
        if not db_holding:
            return False
        
        db_holding.current_holding = False
        await db.commit()
        return True

class AnalyticsService:
    """Service for portfolio analytics and yield calculations"""
    
    @staticmethod
    async def calculate_holding_yields(
        db: AsyncSession,
        holding_id: str,
        current_price: Optional[Decimal] = None
    ) -> Optional[YieldCalculation]:
        """Calculate yield metrics for a holding"""
        
        holding = await HoldingService.get_holding(db, holding_id)
        if not holding:
            return None
        
        result = await db.execute(
            select(FixedIncomeSecurity).filter(FixedIncomeSecurity.id == holding.security_id)
        )
        security = result.scalar_one_or_none()
        if not security:
            return None
        
        # Use purchase price if current price not provided
        price = current_price or holding.purchase_price
        
        # Calculate years to maturity
        today = date.today()
        years_to_maturity = Decimal(str((security.maturity_date - today).days / 365.25))
        
        if years_to_maturity <= 0:
            return YieldCalculation(holding_id=holding_id)
        
        # Current Yield
        annual_coupon = security.face_value * (security.coupon_rate / Decimal("100"))
        current_yield = FinancialCalculator.calculate_current_yield(
            annual_coupon, 
            security.face_value * (price / Decimal("100"))
        )
        
        # Yield to Maturity
        ytm = FinancialCalculator.calculate_ytm(
            security.face_value,
            security.coupon_rate,
            security.coupon_frequency,
            years_to_maturity,
            security.face_value * (price / Decimal("100"))
        )
        
        # Duration and Convexity
        macaulay_duration = None
        modified_duration = None
        convexity = None
        
        if ytm:
            macaulay_duration, modified_duration = FinancialCalculator.calculate_duration(
                security.face_value,
                security.coupon_rate,
                security.coupon_frequency,
                years_to_maturity,
                ytm
            )
            
            convexity = FinancialCalculator.calculate_convexity(
                security.face_value,
                security.coupon_rate,
                security.coupon_frequency,
                years_to_maturity,
                ytm
            )
        
        return YieldCalculation(
            holding_id=holding_id,
            current_yield=current_yield,
            yield_to_maturity=ytm,
            macaulay_duration=macaulay_duration,
            modified_duration=modified_duration,
            convexity=convexity
        )
    
    @staticmethod
    async def calculate_portfolio_valuation(
        db: AsyncSession,
        portfolio_id: str,
        as_of_date: Optional[date] = None
    ) -> Optional[PortfolioValuation]:
        """Calculate portfolio valuation"""
        
        portfolio = await PortfolioService.get_portfolio(db, portfolio_id)
        if not portfolio:
            return None
        
        holdings = await HoldingService.list_holdings(db, portfolio_id, current_only=True)
        
        total_market_value = Decimal("0.0")
        total_cost_basis = Decimal("0.0")
        
        for holding in holdings:
            result = await db.execute(
                select(FixedIncomeSecurity).filter(FixedIncomeSecurity.id == holding.security_id)
            )
            security = result.scalar_one_or_none()
            if security:
                # Market value (using purchase price as proxy)
                market_value = security.face_value * holding.quantity * (holding.purchase_price / Decimal("100"))
                total_market_value += market_value
                total_cost_basis += market_value
        
        unrealized_gain_loss = total_market_value - total_cost_basis
        
        return PortfolioValuation(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date or date.today(),
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            unrealized_gain_loss=unrealized_gain_loss,
            holdings_count=len(holdings)
        )
    
    @staticmethod
    async def calculate_portfolio_analytics(
        db: AsyncSession,
        portfolio_id: str
    ) -> Optional[PortfolioAnalytics]:
        """Calculate portfolio analytics including weighted average yield and duration"""
        
        holdings = await HoldingService.list_holdings(db, portfolio_id, current_only=True)
        if not holdings:
            return PortfolioAnalytics(portfolio_id=portfolio_id)
        
        total_value = Decimal("0.0")
        weighted_yield = Decimal("0.0")
        weighted_duration = Decimal("0.0")
        weighted_convexity = Decimal("0.0")
        weighted_maturity = Decimal("0.0")
        
        for holding in holdings:
            result = await db.execute(
                select(FixedIncomeSecurity).filter(FixedIncomeSecurity.id == holding.security_id)
            )
            security = result.scalar_one_or_none()
            if not security:
                continue
            
            holding_value = security.face_value * holding.quantity
            total_value += holding_value
            
            # Calculate yield for this holding
            yield_calc = await AnalyticsService.calculate_holding_yields(db, holding.id)
            if yield_calc and yield_calc.yield_to_maturity:
                weighted_yield += yield_calc.yield_to_maturity * holding_value
            
            if yield_calc and yield_calc.modified_duration:
                weighted_duration += yield_calc.modified_duration * holding_value
            
            if yield_calc and yield_calc.convexity:
                weighted_convexity += yield_calc.convexity * holding_value
            
            # Years to maturity
            years_to_mat = Decimal(str((security.maturity_date - date.today()).days / 365.25))
            if years_to_mat > 0:
                weighted_maturity += years_to_mat * holding_value
        
        if total_value > 0:
            return PortfolioAnalytics(
                portfolio_id=portfolio_id,
                weighted_average_yield=weighted_yield / total_value,
                portfolio_duration=weighted_duration / total_value,
                portfolio_convexity=weighted_convexity / total_value,
                weighted_average_maturity=weighted_maturity / total_value
            )
        
        return PortfolioAnalytics(portfolio_id=portfolio_id)

class CouponService:
    """Service for coupon schedule generation"""
    
    @staticmethod
    async def generate_coupon_schedule(
        db: AsyncSession,
        holding_id: str
    ) -> List[CouponPaymentSchema]:
        """Generate coupon payment schedule for a holding"""
        
        holding = await HoldingService.get_holding(db, holding_id)
        if not holding:
            return []
        
        result = await db.execute(
            select(FixedIncomeSecurity).filter(FixedIncomeSecurity.id == holding.security_id)
        )
        security = result.scalar_one_or_none()
        if not security:
            return []
        
        # Generate coupon dates from purchase date to maturity
        coupon_dates = FinancialCalculator.generate_coupon_dates(
            security.issue_date,
            security.maturity_date,
            security.coupon_frequency,
            start_from=holding.purchase_date
        )
        
        # Calculate coupon payment amount
        freq_multiplier = FinancialCalculator.get_frequency_multiplier(security.coupon_frequency)
        if freq_multiplier == 0:
            # Zero coupon - return face value at maturity
            payment_amount = security.face_value * holding.quantity
            return [
                CouponPaymentSchema(
                    id=str(datetime.now().timestamp()),
                    holding_id=holding_id,
                    payment_date=security.maturity_date,
                    payment_amount=payment_amount,
                    accrued_days=0,
                    status=PaymentStatus.PROJECTED
                )
            ]
        
        annual_coupon = security.face_value * (security.coupon_rate / Decimal("100"))
        coupon_payment = (annual_coupon / Decimal(str(freq_multiplier))) * holding.quantity
        
        # Create coupon payment schedule
        schedule = []
        prev_date = security.issue_date
        
        for payment_date in coupon_dates:
            accrued_days = (payment_date - prev_date).days
            
            schedule.append(CouponPaymentSchema(
                id=str(datetime.now().timestamp()) + str(len(schedule)),
                holding_id=holding_id,
                payment_date=payment_date,
                payment_amount=coupon_payment,
                accrued_days=accrued_days,
                status=PaymentStatus.PROJECTED if payment_date > date.today() else PaymentStatus.PAID
            ))
            
            prev_date = payment_date
        
        return schedule
