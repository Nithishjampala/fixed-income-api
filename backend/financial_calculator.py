from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, List, Tuple
import numpy as np
from models import CouponFrequency, DayCountConvention

class FinancialCalculator:
    """Financial calculations for fixed income securities"""
    
    @staticmethod
    def get_frequency_multiplier(frequency: CouponFrequency) -> int:
        """Get number of payments per year based on frequency"""
        mapping = {
            CouponFrequency.MONTHLY: 12,
            CouponFrequency.QUARTERLY: 4,
            CouponFrequency.SEMI_ANNUAL: 2,
            CouponFrequency.ANNUAL: 1,
            CouponFrequency.ZERO_COUPON: 0
        }
        return mapping[frequency]
    
    @staticmethod
    def calculate_days_between(start_date: date, end_date: date, convention: DayCountConvention) -> Tuple[int, int]:
        """Calculate days between dates based on day count convention
        Returns: (numerator_days, denominator_days)
        """
        if convention == DayCountConvention.ACT_360:
            actual_days = (end_date - start_date).days
            return actual_days, 360
        elif convention == DayCountConvention.ACT_365:
            actual_days = (end_date - start_date).days
            return actual_days, 365
        elif convention == DayCountConvention.ACT_ACT:
            actual_days = (end_date - start_date).days
            # Simplified - actual days in year
            return actual_days, 365
        elif convention == DayCountConvention.THIRTY_360:
            # 30/360 convention
            d1 = min(start_date.day, 30)
            d2 = min(end_date.day, 30) if d1 == 30 else end_date.day
            days = (end_date.year - start_date.year) * 360 + (end_date.month - start_date.month) * 30 + (d2 - d1)
            return days, 360
        return 0, 365
    
    @staticmethod
    def calculate_current_yield(annual_coupon: Decimal, current_price: Decimal) -> Decimal:
        """Calculate current yield: (annual coupon / current price) * 100"""
        if current_price <= 0:
            return Decimal("0.0")
        return (annual_coupon / current_price) * Decimal("100")
    
    @staticmethod
    def calculate_ytm(
        face_value: Decimal,
        coupon_rate: Decimal,
        frequency: CouponFrequency,
        years_to_maturity: Decimal,
        current_price: Decimal,
        max_iterations: int = 100,
        tolerance: float = 0.0001
    ) -> Optional[Decimal]:
        """Calculate Yield to Maturity using Newton-Raphson method"""
        
        freq_multiplier = FinancialCalculator.get_frequency_multiplier(frequency)
        if freq_multiplier == 0:  # Zero coupon bond
            # YTM = (Face Value / Price)^(1/years) - 1
            if current_price <= 0 or years_to_maturity <= 0:
                return None
            ytm = (float(face_value) / float(current_price)) ** (1 / float(years_to_maturity)) - 1
            return Decimal(str(ytm * 100))
        
        # Coupon payment per period
        coupon_payment = float(face_value) * (float(coupon_rate) / 100) / freq_multiplier
        periods = float(years_to_maturity) * freq_multiplier
        price = float(current_price)
        face = float(face_value)
        
        # Initial guess: approximate yield
        ytm_guess = (coupon_payment + (face - price) / periods) / ((face + price) / 2)
        
        for _ in range(max_iterations):
            # Calculate present value and derivative
            pv = 0
            pv_derivative = 0
            
            for t in range(1, int(periods) + 1):
                discount_factor = (1 + ytm_guess) ** t
                pv += coupon_payment / discount_factor
                pv_derivative += -t * coupon_payment / ((1 + ytm_guess) ** (t + 1))
            
            # Add face value at maturity
            discount_factor = (1 + ytm_guess) ** periods
            pv += face / discount_factor
            pv_derivative += -periods * face / ((1 + ytm_guess) ** (periods + 1))
            
            # Newton-Raphson update
            price_diff = pv - price
            if abs(price_diff) < tolerance:
                # Convert periodic yield to annual percentage
                annual_ytm = ytm_guess * freq_multiplier * 100
                return Decimal(str(round(annual_ytm, 4)))
            
            if pv_derivative == 0:
                return None
            
            ytm_guess = ytm_guess - price_diff / pv_derivative
            
            if ytm_guess < -0.99:  # Prevent negative yield issues
                ytm_guess = 0.01
        
        return None  # Failed to converge
    
    @staticmethod
    def calculate_duration(
        face_value: Decimal,
        coupon_rate: Decimal,
        frequency: CouponFrequency,
        years_to_maturity: Decimal,
        ytm: Decimal
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Calculate Macaulay Duration and Modified Duration
        Returns: (macaulay_duration, modified_duration)
        """
        
        freq_multiplier = FinancialCalculator.get_frequency_multiplier(frequency)
        if freq_multiplier == 0:  # Zero coupon bond
            macaulay = years_to_maturity
            modified = macaulay / (1 + float(ytm) / 100)
            return Decimal(str(macaulay)), Decimal(str(modified))
        
        coupon_payment = float(face_value) * (float(coupon_rate) / 100) / freq_multiplier
        periods = float(years_to_maturity) * freq_multiplier
        periodic_ytm = float(ytm) / 100 / freq_multiplier
        
        weighted_pv = 0
        total_pv = 0
        
        for t in range(1, int(periods) + 1):
            discount_factor = (1 + periodic_ytm) ** t
            pv = coupon_payment / discount_factor
            weighted_pv += (t / freq_multiplier) * pv
            total_pv += pv
        
        # Add face value at maturity
        discount_factor = (1 + periodic_ytm) ** periods
        face_pv = float(face_value) / discount_factor
        weighted_pv += (periods / freq_multiplier) * face_pv
        total_pv += face_pv
        
        if total_pv == 0:
            return None, None
        
        macaulay_duration = weighted_pv / total_pv
        modified_duration = macaulay_duration / (1 + periodic_ytm)
        
        return Decimal(str(round(macaulay_duration, 4))), Decimal(str(round(modified_duration, 4)))
    
    @staticmethod
    def calculate_convexity(
        face_value: Decimal,
        coupon_rate: Decimal,
        frequency: CouponFrequency,
        years_to_maturity: Decimal,
        ytm: Decimal
    ) -> Optional[Decimal]:
        """Calculate convexity of a bond"""
        
        freq_multiplier = FinancialCalculator.get_frequency_multiplier(frequency)
        if freq_multiplier == 0:  # Zero coupon bond
            periodic_ytm = float(ytm) / 100
            periods = float(years_to_maturity)
            convexity = periods * (periods + 1) / ((1 + periodic_ytm) ** 2)
            return Decimal(str(round(convexity, 4)))
        
        coupon_payment = float(face_value) * (float(coupon_rate) / 100) / freq_multiplier
        periods = float(years_to_maturity) * freq_multiplier
        periodic_ytm = float(ytm) / 100 / freq_multiplier
        
        weighted_pv = 0
        total_pv = 0
        
        for t in range(1, int(periods) + 1):
            discount_factor = (1 + periodic_ytm) ** t
            pv = coupon_payment / discount_factor
            weighted_pv += t * (t + 1) * pv
            total_pv += pv
        
        # Add face value at maturity
        discount_factor = (1 + periodic_ytm) ** periods
        face_pv = float(face_value) / discount_factor
        weighted_pv += periods * (periods + 1) * face_pv
        total_pv += face_pv
        
        if total_pv == 0:
            return None
        
        convexity = weighted_pv / (total_pv * (freq_multiplier ** 2) * ((1 + periodic_ytm) ** 2))
        return Decimal(str(round(convexity, 4)))
    
    @staticmethod
    def generate_coupon_dates(
        issue_date: date,
        maturity_date: date,
        frequency: CouponFrequency,
        start_from: Optional[date] = None
    ) -> List[date]:
        """Generate coupon payment dates"""
        
        freq_multiplier = FinancialCalculator.get_frequency_multiplier(frequency)
        if freq_multiplier == 0:  # Zero coupon
            return [maturity_date]
        
        months_between = 12 // freq_multiplier
        coupon_dates = []
        
        current_date = maturity_date
        while current_date > issue_date:
            if start_from is None or current_date >= start_from:
                coupon_dates.append(current_date)
            
            # Move back by payment frequency
            year = current_date.year
            month = current_date.month - months_between
            day = current_date.day
            
            while month < 1:
                month += 12
                year -= 1
            
            try:
                current_date = date(year, month, day)
            except ValueError:
                # Handle end-of-month edge cases
                current_date = date(year, month, 28)
        
        coupon_dates.reverse()
        return coupon_dates
    
    @staticmethod
    def calculate_accrued_interest(
        face_value: Decimal,
        coupon_rate: Decimal,
        frequency: CouponFrequency,
        last_coupon_date: date,
        settlement_date: date,
        convention: DayCountConvention
    ) -> Decimal:
        """Calculate accrued interest from last coupon date to settlement"""
        
        freq_multiplier = FinancialCalculator.get_frequency_multiplier(frequency)
        if freq_multiplier == 0:
            return Decimal("0.0")
        
        # Annual coupon payment
        annual_coupon = float(face_value) * (float(coupon_rate) / 100)
        coupon_payment = annual_coupon / freq_multiplier
        
        # Calculate days accrued
        days_accrued, days_in_period = FinancialCalculator.calculate_days_between(
            last_coupon_date, settlement_date, convention
        )
        
        # Period length in days
        period_length = days_in_period / freq_multiplier
        
        accrued = coupon_payment * (days_accrued / period_length)
        return Decimal(str(round(accrued, 4)))
