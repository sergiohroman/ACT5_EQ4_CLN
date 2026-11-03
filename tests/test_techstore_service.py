"""Ejercicio PIA con adaptador simulado: TechStore no usa servicios externos reales."""
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.techstore import Customer, InvalidOrderData, Money, Order, OrderItem, OrderStatus
from src.techstore_service import confirm_and_publish


class EventPublisher:
    """Puerto: lo que TechStore necesita de un sistema de mensajeria/correo."""

    def publish(self, event):
        raise NotImplementedError


def make_order(active=True):
    order = Order("O001", Customer("C001", active=active))
    order.add_item(OrderItem("SKU001", 1, Money(Decimal("100"))))
    return order


def test_publica_el_evento_despues_de_confirmar():
    publisher = Mock(spec=EventPublisher)
    status = confirm_and_publish(make_order(), publisher)
    assert status == OrderStatus.CONFIRMED
    publisher.publish.assert_called_once()
    assert publisher.publish.call_args.args[0].name == "OrderConfirmed"


def test_no_publica_nada_si_la_confirmacion_falla():
    publisher = Mock(spec=EventPublisher)
    with pytest.raises(InvalidOrderData):
        confirm_and_publish(make_order(active=False), publisher)
    publisher.publish.assert_not_called()


def test_timeout_del_publicador_se_propaga():
    publisher = Mock(spec=EventPublisher)
    publisher.publish.side_effect = TimeoutError("broker no responde")
    with pytest.raises(TimeoutError):
        confirm_and_publish(make_order(), publisher)
