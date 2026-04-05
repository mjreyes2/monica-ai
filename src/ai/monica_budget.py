"""
Monica Budget Manager - Personal finance tracking and visualization.

Features:
- Income and expense tracking by category
- Monthly/weekly budget limits
- Spending analysis and alerts
- Chart generation (pie, bar, line) via matplotlib
- Persistent storage in JSON
- Voice-friendly summaries for TTS
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("Monica.Budget")


@dataclass
class Transaction:
    amount: float
    category: str
    description: str
    date: str  # ISO format
    type: str  # "income" or "expense"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> 'Transaction':
        return Transaction(**d)


class MonicaBudget:
    """Personal budget manager for Monica AI."""

    DEFAULT_EXPENSE_CATEGORIES = [
        "rent", "utilities", "groceries", "dining", "transport",
        "entertainment", "health", "insurance", "subscriptions",
        "clothing", "education", "savings", "gifts", "personal", "other"
    ]

    DEFAULT_INCOME_CATEGORIES = [
        "salary", "freelance", "investments", "gifts", "refunds", "other"
    ]

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "user_profile"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._file = self.data_dir / "budget.json"
        self._charts_dir = self.data_dir / "budget_charts"
        self._charts_dir.mkdir(parents=True, exist_ok=True)

        self.transactions: List[Transaction] = []
        self.monthly_limits: Dict[str, float] = {}
        self.monthly_income_goal: float = 0.0
        self._load()
        logger.info(f"Budget manager loaded: {len(self.transactions)} transactions")

    # ==================== Persistence ====================

    def _load(self):
        try:
            if self._file.exists():
                data = json.loads(self._file.read_text(encoding="utf-8"))
                self.transactions = [Transaction.from_dict(t) for t in data.get("transactions", [])]
                self.monthly_limits = data.get("monthly_limits", {})
                self.monthly_income_goal = data.get("monthly_income_goal", 0.0)
        except Exception as e:
            logger.warning(f"Could not load budget: {e}")

    def _save(self):
        try:
            data = {
                "transactions": [t.to_dict() for t in self.transactions],
                "monthly_limits": self.monthly_limits,
                "monthly_income_goal": self.monthly_income_goal,
            }
            self._file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not save budget: {e}")

    # ==================== Add Transactions ====================

    def add_expense(self, amount: float, category: str, description: str = "") -> str:
        category = category.lower().strip()
        t = Transaction(
            amount=round(abs(amount), 2),
            category=category,
            description=description,
            date=datetime.now().isoformat(),
            type="expense",
        )
        self.transactions.append(t)
        self._save()

        # Check if over budget
        warning = ""
        if category in self.monthly_limits:
            spent = self.get_monthly_spending(category)
            limit = self.monthly_limits[category]
            if spent > limit:
                warning = f" Warning: you've exceeded your {category} budget of ${limit:.2f} by ${spent - limit:.2f}."
            elif spent > limit * 0.8:
                warning = f" Heads up: you've used {spent/limit*100:.0f}% of your {category} budget."

        return f"Added ${t.amount:.2f} expense for {category}.{warning}"

    def add_income(self, amount: float, category: str = "salary", description: str = "") -> str:
        t = Transaction(
            amount=round(abs(amount), 2),
            category=category.lower().strip(),
            description=description,
            date=datetime.now().isoformat(),
            type="income",
        )
        self.transactions.append(t)
        self._save()
        return f"Added ${t.amount:.2f} income from {t.category}."

    def set_budget_limit(self, category: str, amount: float) -> str:
        category = category.lower().strip()
        self.monthly_limits[category] = round(abs(amount), 2)
        self._save()
        return f"Set monthly {category} budget to ${amount:.2f}."

    def set_income_goal(self, amount: float) -> str:
        self.monthly_income_goal = round(abs(amount), 2)
        self._save()
        return f"Set monthly income goal to ${amount:.2f}."

    # ==================== Queries ====================

    def get_monthly_spending(self, category: Optional[str] = None, month: Optional[int] = None, year: Optional[int] = None) -> float:
        now = datetime.now()
        m = month or now.month
        y = year or now.year
        total = 0.0
        for t in self.transactions:
            if t.type != "expense":
                continue
            try:
                dt = datetime.fromisoformat(t.date)
            except Exception:
                continue
            if dt.month == m and dt.year == y:
                if category is None or t.category == category.lower():
                    total += t.amount
        return round(total, 2)

    def get_monthly_income(self, month: Optional[int] = None, year: Optional[int] = None) -> float:
        now = datetime.now()
        m = month or now.month
        y = year or now.year
        total = 0.0
        for t in self.transactions:
            if t.type != "income":
                continue
            try:
                dt = datetime.fromisoformat(t.date)
            except Exception:
                continue
            if dt.month == m and dt.year == y:
                total += t.amount
        return round(total, 2)

    def get_spending_by_category(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, float]:
        now = datetime.now()
        m = month or now.month
        y = year or now.year
        cats: Dict[str, float] = {}
        for t in self.transactions:
            if t.type != "expense":
                continue
            try:
                dt = datetime.fromisoformat(t.date)
            except Exception:
                continue
            if dt.month == m and dt.year == y:
                cats[t.category] = cats.get(t.category, 0.0) + t.amount
        return {k: round(v, 2) for k, v in sorted(cats.items(), key=lambda x: -x[1])}

    def get_summary(self) -> str:
        """Get a voice-friendly budget summary for TTS."""
        now = datetime.now()
        month_name = now.strftime("%B")
        income = self.get_monthly_income()
        spending = self.get_monthly_spending()
        net = income - spending
        by_cat = self.get_spending_by_category()

        parts = [f"Here's your {month_name} budget summary."]
        parts.append(f"Total income: ${income:.2f}. Total spending: ${spending:.2f}.")

        if net >= 0:
            parts.append(f"You're ${net:.2f} in the positive.")
        else:
            parts.append(f"You're ${abs(net):.2f} over budget.")

        if by_cat:
            top = list(by_cat.items())[:3]
            top_str = ", ".join(f"{cat} at ${amt:.2f}" for cat, amt in top)
            parts.append(f"Top spending: {top_str}.")

        # Budget limit warnings
        for cat, limit in self.monthly_limits.items():
            spent = self.get_monthly_spending(cat)
            if spent > limit:
                parts.append(f"You've exceeded your {cat} budget by ${spent - limit:.2f}.")

        return " ".join(parts)

    def get_recent_transactions(self, n: int = 10) -> List[Transaction]:
        return sorted(self.transactions, key=lambda t: t.date, reverse=True)[:n]

    # ==================== Visualizations ====================

    def generate_spending_pie_chart(self) -> Optional[str]:
        """Generate a pie chart of spending by category. Returns file path."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            by_cat = self.get_spending_by_category()
            if not by_cat:
                return None

            fig, ax = plt.subplots(figsize=(8, 6))
            colors = plt.cm.Set3(range(len(by_cat)))
            wedges, texts, autotexts = ax.pie(
                by_cat.values(),
                labels=by_cat.keys(),
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
            )
            for t in autotexts:
                t.set_fontsize(9)
            month_name = datetime.now().strftime("%B %Y")
            ax.set_title(f"Spending by Category - {month_name}", fontsize=14, fontweight='bold')
            plt.tight_layout()

            path = str(self._charts_dir / "spending_pie.png")
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Pie chart saved: {path}")
            return path
        except Exception as e:
            logger.error(f"Pie chart error: {e}")
            return None

    def generate_budget_vs_actual_bar(self) -> Optional[str]:
        """Generate bar chart comparing budget limits vs actual spending."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np_mpl

            if not self.monthly_limits:
                return None

            categories = list(self.monthly_limits.keys())
            limits = [self.monthly_limits[c] for c in categories]
            actuals = [self.get_monthly_spending(c) for c in categories]

            x = np_mpl.arange(len(categories))
            width = 0.35

            fig, ax = plt.subplots(figsize=(10, 6))
            bars1 = ax.bar(x - width/2, limits, width, label='Budget', color='#4CAF50', alpha=0.8)
            bars2 = ax.bar(x + width/2, actuals, width, label='Actual', color='#F44336', alpha=0.8)

            # Color actual bars green if under budget
            for i, (lim, act) in enumerate(zip(limits, actuals)):
                if act <= lim:
                    bars2[i].set_color('#2196F3')

            ax.set_xlabel('Category')
            ax.set_ylabel('Amount ($)')
            month_name = datetime.now().strftime("%B %Y")
            ax.set_title(f"Budget vs Actual Spending - {month_name}", fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()

            path = str(self._charts_dir / "budget_vs_actual.png")
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Budget vs actual chart saved: {path}")
            return path
        except Exception as e:
            logger.error(f"Bar chart error: {e}")
            return None

    def generate_spending_trend(self, months: int = 6) -> Optional[str]:
        """Generate line chart of monthly spending over time."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            now = datetime.now()
            labels = []
            totals = []
            incomes = []
            for i in range(months - 1, -1, -1):
                d = now - timedelta(days=30 * i)
                m, y = d.month, d.year
                labels.append(d.strftime("%b %Y"))
                totals.append(self.get_monthly_spending(month=m, year=y))
                incomes.append(self.get_monthly_income(month=m, year=y))

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(labels, incomes, 'g-o', label='Income', linewidth=2)
            ax.plot(labels, totals, 'r-o', label='Spending', linewidth=2)
            ax.fill_between(labels, totals, alpha=0.15, color='red')
            ax.fill_between(labels, incomes, alpha=0.15, color='green')
            ax.set_xlabel('Month')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Income vs Spending Trend', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            path = str(self._charts_dir / "spending_trend.png")
            fig.savefig(path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Trend chart saved: {path}")
            return path
        except Exception as e:
            logger.error(f"Trend chart error: {e}")
            return None

    def generate_all_charts(self) -> List[str]:
        """Generate all available charts. Returns list of file paths."""
        paths = []
        for fn in [self.generate_spending_pie_chart, self.generate_budget_vs_actual_bar, self.generate_spending_trend]:
            p = fn()
            if p:
                paths.append(p)
        return paths

    # ==================== AI Context ====================

    def get_budget_context(self) -> str:
        """Get budget context string for AI system prompt."""
        if not self.transactions:
            return ""
        summary = self.get_summary()
        return f"\nBUDGET INFO: {summary}\n"

    def parse_budget_command(self, text: str) -> Optional[str]:
        """Parse natural language budget commands. Returns response or None."""
        import re
        t = text.lower().strip()

        # Add expense: "spent $50 on groceries", "add expense $20 dining"
        m = re.search(r'(?:spent|add expense|expense|paid|bought)\s+\$?([\d,.]+)\s+(?:on|for|at)?\s*(\w+)', t)
        if m:
            amount = float(m.group(1).replace(',', ''))
            cat = m.group(2)
            desc = text
            return self.add_expense(amount, cat, desc)

        # Add income: "earned $3000 salary", "add income $500 freelance"
        m = re.search(r'(?:earned|add income|income|received|got paid)\s+\$?([\d,.]+)\s*(?:from|as|for)?\s*(\w*)', t)
        if m:
            amount = float(m.group(1).replace(',', ''))
            cat = m.group(2) if m.group(2) else "salary"
            return self.add_income(amount, cat, text)

        # Set budget: "set grocery budget to $400", "budget $200 for dining"
        m = re.search(r'(?:set|budget)\s+(?:(\w+)\s+budget\s+(?:to|at)\s+\$?([\d,.]+)|\$?([\d,.]+)\s+(?:for|on)\s+(\w+))', t)
        if m:
            if m.group(1) and m.group(2):
                cat, amount = m.group(1), float(m.group(2).replace(',', ''))
            else:
                amount, cat = float(m.group(3).replace(',', '')), m.group(4)
            return self.set_budget_limit(cat, amount)

        # Set income goal
        m = re.search(r'(?:income goal|goal income|set goal)\s+(?:to\s+)?\$?([\d,.]+)', t)
        if m:
            return self.set_income_goal(float(m.group(1).replace(',', '')))

        # Summary
        if any(kw in t for kw in ['budget summary', 'how much have i spent', 'spending summary',
                                   'what did i spend', 'show my budget', 'budget report',
                                   'how is my budget', 'my finances', 'financial summary']):
            return self.get_summary()

        # Generate charts
        if any(kw in t for kw in ['budget chart', 'spending chart', 'visualize',
                                   'show chart', 'budget graph', 'pie chart', 'bar chart',
                                   'show me my budget', 'budget visualization']):
            paths = self.generate_all_charts()
            if paths:
                summary = self.get_summary()
                return f"{summary} I've generated {len(paths)} chart(s) in the budget_charts folder."
            return "No budget data to visualize yet. Add some expenses first."

        return None


# Singleton
_instance: Optional[MonicaBudget] = None

def get_budget_manager() -> MonicaBudget:
    global _instance
    if _instance is None:
        _instance = MonicaBudget()
    return _instance
