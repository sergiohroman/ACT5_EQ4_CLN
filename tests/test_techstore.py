"""PIA TechStore: 4 reglas x (exito, error, limite) + pruebas complementarias."""
from decimal import Decimal

import pytest

from src.techstore import (
    ActivePromotionSpec,
    Customer,
    InvalidOrderData,
    InvalidOrderTransition,
    Money,
    Order,
    OrderItem,
    OrderItemLimitExceeded,
    OrderStatus,
    discount_rate,
)


def mxn(value):
    return Money(Decimal(str(value)))


def make_order(items=(), vip=False, active=True, promo=False, oid="O001"):
    order = Order(oid, Customer("C001", vip=vip, active=active), promotion_active=promo)
    for sku, qty, price in items:
        order.add_item(OrderItem(sku, qty, mxn(price)))
    return order


# ===== R1. Descuento 10 % (VIP + monto > 500 + >= 4 unidades + sin promocion) =====
def test_r1_exito_vip_con_cuatro_unidades_obtiene_10_por_ciento():  # CP-P01
    order = make_order([("SKU001", 2, 600), ("SKU002", 2, 450)], vip=True)  # 2,100 / 4 u
    assert discount_rate(order) == Decimal("0.10")
    assert order.total.amount * discount_rate(order) == Decimal("210.00")


def test_r1_error_promocion_activa_bloquea_descuento():  # CP-P02
    order = make_order([("SKU001", 4, 600)], vip=True, promo=True)
    assert discount_rate(order) == Decimal("0")


def test_r1_limite_total_exacto_500_no_supera_el_umbral():  # CP-P03
    order = make_order([("SKU001", 4, 125)], vip=True)  # exactamente 500.00
    assert order.total.amount == Decimal("500")
    assert discount_rate(order) == Decimal("0")


def test_r1_limite_tres_unidades_no_alcanzan_el_minimo():
    order = make_order([("SKU001", 3, 500)], vip=True)  # 1,500 pero solo 3 u
    assert discount_rate(order) == Decimal("0")


# ===== R2. Maximo 20 unidades (suma cantidades, no renglones) =====
def test_r2_exito_dos_renglones_suman_tres_unidades():  # CP-P04
    order = make_order([("SKU001", 2, 100), ("SKU002", 1, 50)])
    assert order.units == 3


def test_r2_error_21_unidades_se_rechazan_sin_modificar_el_pedido():  # CP-P05
    order = make_order([("SKU001", 19, 10)])
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(OrderItem("SKU002", 2, mxn(10)))
    assert order.units == 19 and len(order.items) == 1


def test_r2_limite_exactamente_20_unidades_se_permiten():  # CP-P06
    order = make_order([("SKU001", 5, 10)] * 4)  # 4 renglones x 5 = 20
    assert order.units == 20


# ===== R3. Confirmar requiere articulos y cliente activo =====
def test_r3_exito_confirma_y_registra_evento():  # CP-P07
    order = make_order([("SKU001", 2, 100)])
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_r3_error_cliente_inactivo_no_confirma_ni_emite_evento():  # CP-P08
    order = make_order([("SKU001", 2, 100)], active=False)
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status == OrderStatus.DRAFT and order.events == []


def test_r3_limite_pedido_minimo_de_una_unidad_confirma():  # CP-P09
    order = make_order([("SKU001", 1, 1)])
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED


def test_r3_pedido_vacio_no_confirma():
    order = make_order()
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.events == []


def test_r3_confirmacion_doble_no_agrega_evento():
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.confirm()
    assert len(order.events) == 1


# ===== R4. Cancelar solo desde CONFIRMED y con motivo =====
def test_r4_exito_cancela_pedido_confirmado_con_motivo():  # CP-P10
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    order.cancel("cliente se arrepintio")
    assert order.status == OrderStatus.CANCELLED
    assert order.events[-1].name == "OrderCancelled"


def test_r4_error_no_se_cancela_un_pedido_enviado():  # CP-P11
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    order.ship("MX-0001")
    with pytest.raises(InvalidOrderTransition):
        order.cancel("tarde")
    assert order.status == OrderStatus.SHIPPED
    assert "OrderCancelled" not in [e.name for e in order.events]


def test_r4_limite_motivo_vacio_o_en_blanco_se_rechaza():  # CP-P12
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    for reason in ("", "   ", None):
        with pytest.raises(InvalidOrderData):
            order.cancel(reason)
    assert order.status == OrderStatus.CONFIRMED


# ===== Complementarias: invariantes, transiciones y specifications =====
def test_money_rechaza_negativos_float_y_no_finitos():
    for bad in (Decimal("-1"), 10.5, Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(InvalidOrderData):
            Money(bad)


def test_money_es_inmutable_y_se_compara_por_valor():
    assert mxn(100) == mxn(100)
    with pytest.raises(AttributeError):
        mxn(100).amount = Decimal("1")


def test_money_no_suma_monedas_distintas():
    with pytest.raises(InvalidOrderData):
        mxn(1).add(Money(Decimal("1"), "USD"))


def test_order_item_valida_cantidad_y_sku():
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU001", 0, mxn(1))
    with pytest.raises(InvalidOrderData):
        OrderItem("", 1, mxn(1))


def test_solo_se_agregan_articulos_en_draft():
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.add_item(OrderItem("SKU002", 1, mxn(1)))


def test_solo_se_aceptan_articulos_en_mxn():
    order = make_order()
    with pytest.raises(InvalidOrderData):
        order.add_item(OrderItem("SKU001", 1, Money(Decimal("1"), "USD")))


def test_flujo_completo_hasta_entregado():
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    order.ship("MX-0002")
    order.deliver()
    assert order.status == OrderStatus.DELIVERED
    assert [e.name for e in order.events] == [
        "OrderConfirmed", "OrderShipped", "OrderDelivered"]


def test_devolucion_desde_enviado():
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    order.ship("MX-0003")
    order.return_order()
    assert order.status == OrderStatus.RETURNED


def test_enviar_sin_guia_se_rechaza():
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.ship("")
    assert order.status == OrderStatus.CONFIRMED


def test_entregar_o_devolver_requiere_estado_enviado():
    order = make_order([("SKU001", 1, 100)])
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.deliver()
    with pytest.raises(InvalidOrderTransition):
        order.return_order()


def test_descuento_5_por_ciento_y_prioridad_del_10():
    grande = make_order([("SKU008", 1, 18000)])
    assert discount_rate(grande) == Decimal("0.05")
    vip_grande = make_order([("SKU008", 4, 5000)], vip=True)
    assert discount_rate(vip_grande) == Decimal("0.10")  # ambas aplican: gana el 10 %


def test_specs_se_componen_con_and_or_not_sin_modificar_el_pedido():
    order = make_order([("SKU001", 1, 100)], promo=True)
    before = (order.status, order.units, order.total)
    assert ActivePromotionSpec().is_satisfied_by(order)
    assert not (~ActivePromotionSpec()).is_satisfied_by(order)
    assert (ActivePromotionSpec() | ~ActivePromotionSpec()).is_satisfied_by(order)
    assert (order.status, order.units, order.total) == before


def test_specification_base_es_abstracta():
    from src.techstore import Specification

    with pytest.raises(NotImplementedError):
        Specification().is_satisfied_by(make_order())
