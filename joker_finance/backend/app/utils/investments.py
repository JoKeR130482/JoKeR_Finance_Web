from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
from scipy.optimize import xirr


class InvestmentCalculator:
    """Калькулятор инвестиционных расчётов"""
    
    @staticmethod
    def calculate_fifo_pnl(
        purchases: List[Dict],
        sales: List[Dict],
        current_quantity: float,
        current_price: float
    ) -> Dict:
        """
        Расчёт PnL по методу FIFO
        
        :param purchases: Список покупок [{date, quantity, price, commission}, ...]
        :param sales: Список продаж [{date, quantity, price, commission}, ...]
        :param current_quantity: Текущее количество активов
        :param current_price: Текущая цена актива
        :return: {total_pnl, realized_pnl, unrealized_pnl, average_cost}
        """
        # Сортируем покупки по дате
        sorted_purchases = sorted(purchases, key=lambda x: x['date'])
        
        # Копируем для обработки
        remaining_purchases = [
            {'quantity': p['quantity'], 'price': p['price'], 'commission': p.get('commission', 0)}
            for p in sorted_purchases
        ]
        
        total_cost = 0.0
        realized_pnl = 0.0
        
        # Обрабатываем продажи
        for sale in sales:
            sale_quantity = sale['quantity']
            sale_price = sale['price']
            sale_commission = sale.get('commission', 0)
            
            sale_revenue = sale_quantity * sale_price - sale_commission
            
            # Списываем с покупок по FIFO
            while sale_quantity > 0 and remaining_purchases:
                purchase = remaining_purchases[0]
                
                if purchase['quantity'] <= sale_quantity:
                    # Полностью используем покупку
                    cost = purchase['quantity'] * purchase['price'] + purchase['commission']
                    realized_pnl += sale_revenue * (purchase['quantity'] / sale_quantity) - cost
                    sale_quantity -= purchase['quantity']
                    remaining_purchases.pop(0)
                else:
                    # Частично используем покупку
                    cost = sale_quantity * purchase['price'] + purchase['commission'] * (sale_quantity / purchase['quantity'])
                    realized_pnl += sale_revenue - cost
                    purchase['quantity'] -= sale_quantity
                    sale_quantity = 0
        
        # Оставшаяся стоимость
        remaining_cost = sum(
            p['quantity'] * p['price'] + p['commission']
            for p in remaining_purchases
        )
        
        # Нереализованный PnL
        unrealized_pnl = current_quantity * current_price - remaining_cost
        
        # Общий PnL
        total_pnl = realized_pnl + unrealized_pnl
        
        # Средняя стоимость
        total_quantity = sum(p['quantity'] for p in remaining_purchases)
        average_cost = remaining_cost / total_quantity if total_quantity > 0 else 0
        
        return {
            'total_pnl': total_pnl,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'average_cost': average_cost,
            'current_value': current_quantity * current_price
        }
    
    @staticmethod
    def calculate_irr(cash_flows: List[Dict]) -> float:
        """
        Расчёт IRR (внутренней нормы доходности)
        
        :param cash_flows: Список денежных потоков [{date, amount}, ...]
                          amount < 0 для вложений, > 0 для выплат
        :return: Годовая доходность в процентах
        """
        if not cash_flows or len(cash_flows) < 2:
            return 0.0
        
        # Сортируем по дате
        sorted_flows = sorted(cash_flows, key=lambda x: x['date'])
        
        # Преобразуем в формат для xirr
        dates = [f['date'] for f in sorted_flows]
        amounts = [f['amount'] for f in sorted_flows]
        
        try:
            irr = xirr(amounts, dates)
            return irr * 100  # В процентах
        except Exception:
            return 0.0
    
    @staticmethod
    def calculate_deposit_yield(
        principal: float,
        interest_rate: float,
        term_months: int,
        compounding: str = 'monthly'
    ) -> Dict:
        """
        Расчёт доходности депозита
        
        :param principal: Основная сумма
        :param interest_rate: Годовая ставка в процентах
        :param term_months: Срок в месяцах
        :param compounding: Тип капитализации (monthly, quarterly, yearly, none)
        :return: {final_amount, total_interest, effective_rate}
        """
        rate = interest_rate / 100
        
        if compounding == 'none':
            # Простые проценты
            total_interest = principal * rate * (term_months / 12)
            final_amount = principal + total_interest
        elif compounding == 'monthly':
            n = 12
            final_amount = principal * (1 + rate / n) ** (n * term_months / 12)
            total_interest = final_amount - principal
        elif compounding == 'quarterly':
            n = 4
            final_amount = principal * (1 + rate / n) ** (n * term_months / 12)
            total_interest = final_amount - principal
        elif compounding == 'yearly':
            n = 1
            final_amount = principal * (1 + rate / n) ** (n * term_months / 12)
            total_interest = final_amount - principal
        else:
            raise ValueError(f"Unknown compounding type: {compounding}")
        
        # Эффективная ставка
        effective_rate = ((final_amount / principal) ** (12 / term_months) - 1) * 100
        
        return {
            'final_amount': final_amount,
            'total_interest': total_interest,
            'effective_rate': effective_rate
        }
