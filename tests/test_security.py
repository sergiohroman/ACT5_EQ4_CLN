from datetime import datetime, timedelta, timezone

import pytest

from src.security import can_cancel

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)  # fecha fija: sin resultados variables


def test_owner_within_24h():
    assert can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=1), NOW)


def test_stranger_denied():
    assert not can_cancel("NEW", 1, 2, False, NOW, NOW)


def test_shipped_denied_even_admin():
    assert not can_cancel("SHIPPED", 1, 1, True, NOW, NOW)


def test_expired_denied():
    assert not can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=25), NOW)


def test_admin_cancels_new_order_of_another_user():
    assert can_cancel("NEW", 1, 99, True, NOW - timedelta(days=30), NOW)


def test_owner_denied_at_exactly_24h():
    assert not can_cancel("NEW", 1, 1, False, NOW - timedelta(hours=24), NOW)


def test_owner_allowed_one_second_before_24h():
    created = NOW - timedelta(hours=24) + timedelta(seconds=1)
    assert can_cancel("NEW", 1, 1, False, created, NOW)


def test_default_now_uses_current_time():
    created = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert can_cancel("NEW", 1, 1, False, created)  # sin 'now' explícito


@pytest.mark.parametrize(
    "status,owner,user,admin,age_h,allowed",
    [
        ("NEW", 1, 1, False, 1, True),          # dueño, dentro de 24 h
        ("NEW", 1, 1, False, 24, False),        # dueño, límite exacto
        ("NEW", 1, 1, False, 48, False),        # dueño, vencido
        ("NEW", 1, 2, False, 1, False),         # tercero
        ("NEW", 1, 2, True, 1, True),           # administrador
        ("CONFIRMED", 1, 2, True, 100, True),   # administrador, pedido confirmado
        ("SHIPPED", 1, 1, False, 1, False),     # enviado, dueño
        ("SHIPPED", 1, 2, True, 1, False),      # enviado, administrador
    ],
)
def test_authorization_matrix(status, owner, user, admin, age_h, allowed):
    created = NOW - timedelta(hours=age_h)
    assert can_cancel(status, owner, user, admin, created, NOW) is allowed
