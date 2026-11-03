"""Adaptador simulado (ejercicio PIA): publicar eventos de dominio hacia un servicio externo."""


def confirm_and_publish(order, publisher):
    """Confirma el pedido y SOLO despues publica los eventos registrados.

    Si confirm() lanza una excepcion de dominio no se publica nada.
    """
    order.confirm()
    for event in list(order.events):
        publisher.publish(event)
    return order.status
