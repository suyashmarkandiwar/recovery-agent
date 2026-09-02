# tests/test_tone_logic.py

import pytest
from datetime import date, timedelta, datetime, timezone
from sqlmodel import Session, select, col, or_

from app.agent.tone_logic import determine_tone
from app.db.models import Invoice, AuditLog
from app.db.database import engine   # real DB


# ─────────────────────────────────────────────
# 1. TONE BRACKET UNIT TESTS (pure function)
# ─────────────────────────────────────────────

class TestToneBrackets:
    def test_0_days_returns_none(self):
        assert determine_tone(0) is None

    def test_10_days_returns_none(self):
        assert determine_tone(10) is None

    def test_11_days_polite(self):
        assert determine_tone(11) == "polite and gentle reminder"

    def test_20_days_polite(self):
        assert determine_tone(20) == "polite and gentle reminder"

    def test_21_days_firm(self):
        assert determine_tone(21) == "firm but professional reminder"

    def test_30_days_firm(self):
        assert determine_tone(30) == "firm but professional reminder"

    def test_31_days_escalate(self):
        assert determine_tone(31) == "ESCALATE"

    def test_100_days_escalate(self):
        assert determine_tone(100) == "ESCALATE"


# ─────────────────────────────────────────────
# 2. COOLDOWN LOGIC TESTS (pure logic, no DB)
# ─────────────────────────────────────────────

class TestCooldownLogic:
    """Tests the 4-day cooldown rule as a standalone function."""

    def _should_skip_cooldown(self, last_contacted: date | None, today: date) -> bool:
        """Mirrors the cooldown logic in scheduler.py."""
        if last_contacted and (today - last_contacted).days < 4:
            return True
        return False

    def test_contacted_3_days_ago_should_skip(self):
        today = date.today()
        last_contacted = today - timedelta(days=3)
        assert self._should_skip_cooldown(last_contacted, today) is True

    def test_contacted_4_days_ago_should_not_skip(self):
        today = date.today()
        last_contacted = today - timedelta(days=4)
        assert self._should_skip_cooldown(last_contacted, today) is False

    def test_contacted_today_should_skip(self):
        today = date.today()
        assert self._should_skip_cooldown(today, today) is True

    def test_never_contacted_should_not_skip(self):
        assert self._should_skip_cooldown(None, date.today()) is False


# ─────────────────────────────────────────────
# 3. requires_call DEDUP TEST (real DB)
# ─────────────────────────────────────────────

@pytest.fixture
def real_session():
    """Yields a real DB session and cleans up test invoices after each test."""
    seeded_ids: list[int] = []
    with Session(engine) as session:
        yield session, seeded_ids
        # Cleanup: delete only the invoices seeded by this test
        for inv_id in seeded_ids:
            inv = session.get(Invoice, inv_id)
            if inv:
                session.delete(inv)
        session.commit()


class TestRequiresCallDedup:
    def test_escalated_invoice_is_skipped_by_scheduler(self, real_session):
        """
        An invoice with requires_call=True should be excluded from the scheduler query.
        """
        session, seeded_ids = real_session
        today = date.today()

        invoice = Invoice(
            client_name="TEST_escalated",
            client_email="test_esc@test.com",
            amount=5000.0,
            due_date=today - timedelta(days=40),
            status="OVERDUE",
            requires_call=True
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        assert invoice.id is not None
        seeded_ids.append(invoice.id)

        results = session.exec(
            select(Invoice).where(
                Invoice.status == "OVERDUE",
                col(Invoice.requires_call).is_(False),
                or_(Invoice.pause_followups_until == None,
                    col(Invoice.pause_followups_until) < today)
            )
        ).all()

        assert invoice.id not in [inv.id for inv in results]

    def test_non_escalated_invoice_is_included(self, real_session):
        """
        An OVERDUE invoice with requires_call=False should be picked up.
        """
        session, seeded_ids = real_session
        today = date.today()

        invoice = Invoice(
            client_name="TEST_normal",
            client_email="test_norm@test.com",
            amount=3000.0,
            due_date=today - timedelta(days=15),
            status="OVERDUE",
            requires_call=False
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        assert invoice.id is not None
        seeded_ids.append(invoice.id)

        results = session.exec(
            select(Invoice).where(
                Invoice.status == "OVERDUE",
                col(Invoice.requires_call).is_(False),
                or_(Invoice.pause_followups_until == None,
                    col(Invoice.pause_followups_until) < today)
            )
        ).all()

        assert invoice.id in [inv.id for inv in results]

    def test_paused_invoice_is_skipped(self, real_session):
        """
        An invoice with pause_followups_until in the future should be excluded.
        """
        session, seeded_ids = real_session
        today = date.today()

        invoice = Invoice(
            client_name="TEST_paused",
            client_email="test_paused@test.com",
            amount=2000.0,
            due_date=today - timedelta(days=15),
            status="OVERDUE",
            requires_call=False,
            pause_followups_until=today + timedelta(days=5)
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        assert invoice.id is not None
        seeded_ids.append(invoice.id)

        results = session.exec(
            select(Invoice).where(
                Invoice.status == "OVERDUE",
                col(Invoice.requires_call).is_(False),
                or_(Invoice.pause_followups_until == None,
                    col(Invoice.pause_followups_until) < today)
            )
        ).all()

        assert invoice.id not in [inv.id for inv in results]
