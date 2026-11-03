"""Nucleo de negocio TechStore (PIA, Actividad 4) adaptado para pruebas de la Unidad 5.

NOTA: reconstruido a partir del reporte de la Actividad 4. Si tu repositorio
ACT4_EQ4_CLN tiene firmas distintas, ajusta los imports/constructores de
tests/test_techstore*.py; las reglas y los casos de prueba siguen siendo los mismos.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

MAX_UNITS = 20


class DomainException(Exception):
    pass


class InvalidOrderData(DomainException):
    pass


class InvalidOrderTransition(DomainException):
    pass


class OrderItemLimitExceeded(DomainException):
    pass


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "MXN"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise InvalidOrderData("El monto debe ser Decimal, no float")
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidOrderData("El monto no puede ser negativo ni no finito")

    def add(self, other):
        if self.currency != other.currency:
            raise InvalidOrderData("No se suman monedas distintas")
        return Money(self.amount + other.amount, self.currency)

    def times(self, factor):
        return Money(self.amount * factor, self.currency)


@dataclass(frozen=True)
class Customer:
    id: str
    vip: bool = False
    active: bool = True


@dataclass(frozen=True)
class OrderItem:
    sku: str
    quantity: int
    unit_price: Money

    def __post_init__(self):
        if self.quantity <= 0:
            raise InvalidOrderData("La cantidad debe ser mayor a 0")
        if not self.sku:
            raise InvalidOrderData("El SKU no puede estar vacio")

    @property
    def subtotal(self):
        return self.unit_price.times(self.quantity)


class OrderStatus(Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


@dataclass(frozen=True)
class DomainEvent:
    name: str
    order_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Order:
    id: str
    customer: Customer
    promotion_active: bool = False
    status: OrderStatus = OrderStatus.DRAFT
    items: list = field(default_factory=list)
    events: list = field(default_factory=list)

    @property
    def units(self):
        return sum(item.quantity for item in self.items)

    @property
    def total(self):
        result = Money(Decimal("0"))
        for item in self.items:
            result = result.add(item.subtotal)
        return result

    def _require(self, expected, action):
        if self.status != expected:
            raise InvalidOrderTransition(f"Solo se puede {action} desde {expected.value}")

    def _record(self, name):
        self.events.append(DomainEvent(name, self.id))

    def add_item(self, item):
        if self.status != OrderStatus.DRAFT:
            raise InvalidOrderTransition("Solo DRAFT admite articulos")
        if item.unit_price.currency != "MXN":
            raise InvalidOrderData("Solo MXN")
        if self.units + item.quantity > MAX_UNITS:  # suma unidades, no renglones
            raise OrderItemLimitExceeded("Maximo 20 unidades")
        self.items.append(item)

    def confirm(self):
        self._require(OrderStatus.DRAFT, "confirmar")
        if not self.items or not self.customer.active:
            raise InvalidOrderData("Requiere articulos y cliente activo")
        self.status = OrderStatus.CONFIRMED
        self._record("OrderConfirmed")

    def ship(self, tracking):
        self._require(OrderStatus.CONFIRMED, "enviar")
        if not tracking or not tracking.strip():
            raise InvalidOrderData("El envio requiere numero de guia")
        self.status = OrderStatus.SHIPPED
        self._record("OrderShipped")

    def cancel(self, reason):
        self._require(OrderStatus.CONFIRMED, "cancelar")
        if not reason or not reason.strip():
            raise InvalidOrderData("La cancelacion requiere motivo")
        self.status = OrderStatus.CANCELLED
        self._record("OrderCancelled")

    def deliver(self):
        self._require(OrderStatus.SHIPPED, "entregar")
        self.status = OrderStatus.DELIVERED
        self._record("OrderDelivered")

    def return_order(self):
        self._require(OrderStatus.SHIPPED, "devolver")
        self.status = OrderStatus.RETURNED
        self._record("OrderReturned")


# ---------------- Specification Pattern ----------------
class Specification:
    def is_satisfied_by(self, order):
        raise NotImplementedError

    def __and__(self, other):
        return AndSpec(self, other)

    def __or__(self, other):
        return OrSpec(self, other)

    def __invert__(self):
        return NotSpec(self)


class AndSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order):
        return self.left.is_satisfied_by(order) and self.right.is_satisfied_by(order)


class OrSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order):
        return self.left.is_satisfied_by(order) or self.right.is_satisfied_by(order)


class NotSpec(Specification):
    def __init__(self, inner):
        self.inner = inner

    def is_satisfied_by(self, order):
        return not self.inner.is_satisfied_by(order)


class MinimumAmountSpec(Specification):
    def __init__(self, threshold):
        self.threshold = Decimal(threshold)

    def is_satisfied_by(self, order):
        return order.total.amount > self.threshold  # estrictamente mayor


class VIPCustomerSpec(Specification):
    def is_satisfied_by(self, order):
        return order.customer.vip


class MinimumUnitsSpec(Specification):
    def __init__(self, minimum):
        self.minimum = minimum

    def is_satisfied_by(self, order):
        return order.units >= self.minimum


class ActivePromotionSpec(Specification):
    def is_satisfied_by(self, order):
        return order.promotion_active


ten_percent = (MinimumAmountSpec(500) & VIPCustomerSpec()
               & MinimumUnitsSpec(4) & ~ActivePromotionSpec())
five_percent = MinimumAmountSpec(5000) & ~ActivePromotionSpec()


def discount_rate(order):
    """Si se cumplen ambas reglas, aplica primero la del 10 %."""
    if ten_percent.is_satisfied_by(order):
        return Decimal("0.10")
    if five_percent.is_satisfied_by(order):
        return Decimal("0.05")
    return Decimal("0")
