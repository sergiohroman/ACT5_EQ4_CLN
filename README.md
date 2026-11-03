# Unidad 5 · CLN · Integración, pruebas y calidad (Equipo 4)

Proyecto base de pedidos (`src/domain.py`, `application.py`, `repository.py`, `security.py`)
con pruebas unitarias, de integración (SQLAlchemy + SQLite en memoria), con mocks y de
autorización, más la adaptación al PIA **TechStore** (`src/techstore.py`).

## Instalación y ejecución
Windows (PowerShell):
```
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1      # en CMD: .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```
macOS / Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

```
python -m pytest -v
python -m ruff check src tests scripts
python -m pytest -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80
python scripts/generar_matriz_resultados.py     # escribe docs/matriz_resultados.csv
```
El reporte HTML queda en `htmlcov/index.html`.

## Arquitectura
`Application Service -> Dominio (sin ORM) -> puertos (pasarela, repositorio, publicador)`.
El dominio no importa SQLAlchemy (hay una prueba que lo verifica). Las pruebas unitarias no
usan base de datos; las de integración crean un SQLite en memoria por prueba; los servicios
externos se sustituyen con `Mock(spec=...)`.

## Mapa de pruebas
| Archivo | Qué comprueba |
| --- | --- |
| `tests/test_order.py` | Reglas del dominio + ciclo TDD (no confirmar dos veces) |
| `tests/test_matriz_csv.py` | 12 casos de `data/matriz_pruebas.csv` (5 éxito, 4 error, 3 límite) |
| `tests/test_repository.py` | commit, rollback, unicidad, NOT NULL, aislamiento |
| `tests/test_service.py` | Pago aprobado, rechazado, timeout; riesgo de consistencia (xfail) |
| `tests/test_security.py` | Matriz de autorización y límite de 24 h con fechas fijas |
| `tests/test_techstore.py` | PIA: 4 reglas x (éxito, error, límite) + invariantes |
| `tests/test_techstore_service.py` | PIA: adaptador simulado de eventos |

## Decisiones y limitaciones
* SQLite en memoria no sustituye pruebas contra PostgreSQL (ampliación opcional con Docker).
* `test_order_should_not_stay_confirmed_when_payment_rejected` está marcado `xfail(strict=True)`:
  documenta un defecto conocido del código base (confirma antes de cobrar).
* Cobertura de líneas no equivale a ausencia de defectos.
* Datos ficticios; no hay credenciales ni datos personales.
