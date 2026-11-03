# Registro de uso de IA (Vibe Coding responsable)

**Herramienta:** Claude (Anthropic) · **Fecha:** 03/11/2026

## Prompt usado
> Analiza esta clase de dominio y estas reglas aprobadas. Propón casos de prueba pytest para
> éxito, error y límites. No inventes reglas nuevas. Señala supuestos, riesgos y ramas sin
> cobertura. Devuelve pruebas pequeñas y explica qué verifica cada una.

## Resultado de la IA (resumen)
Casos de éxito/error/límite para `Order.confirm`, mock de pasarela (aprobado, rechazado, timeout),
matriz de autorización con fecha fija y pruebas de commit/rollback/unicidad.

## Corrección manual (completa con tu propio criterio)
| Caso sugerido | Decisión | Motivo |
| --- | --- | --- |
| "El administrador puede cancelar un pedido SHIPPED" (así aparece en la presentación) | **Rechazado / corregido** | `can_cancel` implementa que un pedido enviado nunca se cancela, ni por administrador. Se probó lo que el código realmente hace y se dejó el tema como decisión de negocio por discutir. |
| Confirmar con total 0.01 VIP esperando cobro 0.0 | **Corregido** | El descuento redondeado es 0.00, así que el cobro es 0.01. |
| `test_order_should_not_stay_confirmed_when_payment_rejected` | **Aceptado como `xfail` estricto** | Documenta un riesgo real del código base sin ocultarlo. |

## Prueba añadida a partir de lo anterior
`test_owner_denied_at_exactly_24h`, `test_unique_id_is_enforced`, `test_timeout_del_publicador_se_propaga`.

> Antes de entregar: ejecuta tu propia sesión con la IA, sustituye el prompt/resultado si es
> distinto y verifica que cada prueba coincide con las reglas aprobadas.
