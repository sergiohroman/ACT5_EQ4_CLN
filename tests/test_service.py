from unittest.mock import Mock

import pytest

from src.application import OrderService
from src.domain import CustomerHasDebt, Order


class PaymentGateway:
    """Contrato (puerto) que debe cumplir cualquier pasarela real o falsa."""

    def charge(self, amount):
        raise NotImplementedError


def make_gateway(result=True):
    gateway = Mock(spec=PaymentGateway)  # solo permite lo que declara el contrato
    gateway.charge.return_value = result
    return gateway


def test_gateway_approved():
    gateway = Mock()
    gateway.charge.return_value = True
    assert OrderService(gateway).checkout(Order(100)) == 100
    gateway.charge.assert_called_once_with(100)


def test_gateway_rejected():
    gateway = Mock()
    gateway.charge.return_value = False
    with pytest.raises(RuntimeError):
        OrderService(gateway).checkout(Order(100))


def test_vip_rejected_charges_170_and_raises():
    gateway = make_gateway(result=False)
    with pytest.raises(RuntimeError, match="payment rejected"):
        OrderService(gateway).checkout(Order(200, vip=True))
    gateway.charge.assert_called_once_with(170)


def test_vip_approved_charges_discounted_amount():
    gateway = make_gateway(result=True)
    assert OrderService(gateway).checkout(Order(200, vip=True)) == 170
    gateway.charge.assert_called_once_with(170)


def test_gateway_timeout_propagates():
    gateway = make_gateway()
    gateway.charge.side_effect = TimeoutError("gateway timeout")
    with pytest.raises(TimeoutError):
        OrderService(gateway).checkout(Order(100))
    gateway.charge.assert_called_once_with(100)


def test_invalid_order_never_reaches_gateway():
    gateway = make_gateway()
    with pytest.raises(ValueError):
        OrderService(gateway).checkout(Order(0))
    gateway.charge.assert_not_called()  # no se cobra un pedido inválido


def test_customer_with_debt_never_reaches_gateway():
    gateway = make_gateway()
    order = Order(100)
    with pytest.raises(CustomerHasDebt):
        order.confirm(customer_debt=10)
    gateway.charge.assert_not_called()


@pytest.mark.xfail(
    strict=True,
    reason="RIESGO CONOCIDO: checkout() confirma el pedido antes de saber si el pago fue aceptado",
)
def test_order_should_not_stay_confirmed_when_payment_rejected():
    order = Order(100)
    with pytest.raises(RuntimeError):
        OrderService(make_gateway(result=False)).checkout(order)
    assert order.status == "NEW"  # hoy es CONFIRMED: de ahí el xfail documentado
