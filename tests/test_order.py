import pytest

from src.domain import CustomerHasDebt, Order


# ---------- Éxito ----------
def test_vip_discount():
    o = Order(100, vip=True)
    assert o.confirm() == 86
    assert o.status == "CONFIRMED"


def test_regular_no_discount():
    assert Order(100).confirm() == 100


def test_vip_200_charges_170():
    order = Order(200, vip=True)
    assert order.confirm() == 170
    assert order.discount == 30


def test_regular_200_charges_200():
    order = Order(200)
    assert order.confirm() == 200
    assert order.discount == 0


# ---------- Error ----------
def test_customer_debt():
    with pytest.raises(CustomerHasDebt):
        Order(100).confirm(customer_debt=50)


def test_debt_does_not_change_state():
    order = Order(100, vip=True)
    with pytest.raises(CustomerHasDebt):
        order.confirm(customer_debt=1)
    assert order.status == "NEW"
    assert order.discount == 0


@pytest.mark.parametrize("total", [0, -1])
def test_invalid_total(total):
    with pytest.raises(ValueError):
        Order(total).confirm()


# ---------- Límite ----------
def test_minimum_positive_total_is_valid():
    assert Order(0.01).confirm() == pytest.approx(0.01)


def test_zero_debt_is_not_debt():
    assert Order(100).confirm(customer_debt=0) == 100


# ---------- TDD: regla nueva (RED -> GREEN -> REFACTOR) ----------
def test_cannot_confirm_twice():
    order = Order(100)
    order.confirm()
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm()


def test_second_confirm_keeps_discount_and_status():
    order = Order(100, vip=True)
    order.confirm()
    with pytest.raises(ValueError):
        order.confirm()
    assert order.status == "CONFIRMED"
    assert order.discount == 15
