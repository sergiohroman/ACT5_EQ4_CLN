# Guía para capturar tus evidencias REALES (E1–E9)

Las capturas deben salir de TU computadora y TU GitHub. Orden recomendado:

## E1 · Instalación
Ejecuta los comandos del README y captura `python -m pytest -v` con el resumen final.

## E3 · TDD (RED → GREEN → REFACTOR) — la captura roja hay que provocarla
1. Haz primero `git init && git add . && git commit -m "Unidad 5 completa"`.
2. En `src/domain.py`, dentro de `_ensure_can_confirm`, comenta estas dos líneas:
   `if self.status == "CONFIRMED":` y `raise ValueError("already confirmed")`.
3. `python -m pytest tests/test_order.py::test_cannot_confirm_twice -v`  → **RED** (captura).
4. Descomenta las dos líneas → mismo comando → **GREEN** (captura). Luego `python -m pytest -v`.
5. Refactor: ya está aplicado (`_ensure_can_confirm`); corre toda la suite otra vez.
   (Alternativa: `git checkout src/domain.py` para restaurar.)

## E7 · Cobertura
`python -m pytest -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80`
Captura el resumen y `htmlcov/index.html`. Elige una línea/rama sin cubrir y explícala
(ej.: `Specification.is_satisfied_by` base solo lanza NotImplementedError).

## E8 · GitHub Actions (verde → rojo → verde)
1. Crea el repo y haz push (comandos en el laboratorio, paso 8). Captura Actions en verde.
2. Cambia una aserción (p. ej. `assert o.confirm() == 85` → `== 86`), commit + push → captura roja
   y qué paso falló (pytest).
3. Revierte (`git revert HEAD`), push → captura verde.
4. Opcional: Settings → Branches → rule para exigir CI antes de merge (el YAML solo no bloquea).

## E4/E5/E6/E9
Salidas con `python -m pytest tests/test_repository.py -v`, `tests/test_service.py -v`,
`tests/test_security.py -v` y `tests/test_techstore.py -v`.
No incluyas `.venv`, tokens ni credenciales.
