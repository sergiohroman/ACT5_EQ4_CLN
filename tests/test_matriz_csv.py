"""Pruebas parametrizadas: cada fila de data/matriz_pruebas.csv es un caso de prueba."""
import csv
from pathlib import Path

import pytest

from src.domain import CustomerHasDebt, Order

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "matriz_pruebas.csv"
EXCEPTIONS = {"CustomerHasDebt": CustomerHasDebt, "ValueError": ValueError}


def load_cases():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


CASES = load_cases()


def test_matrix_has_required_distribution():
    kinds = [row["tipo"] for row in CASES]
    assert len(CASES) >= 12
    assert kinds.count("exito") >= 5
    assert kinds.count("error") >= 4
    assert kinds.count("limite") >= 3


@pytest.mark.parametrize("row", CASES, ids=[row["caso_id"] for row in CASES])
def test_matrix_case(row):
    order = Order(float(row["total"]), vip=row["vip"] == "1", status=row["estado_inicial"])
    debt = float(row["deuda"])
    expected = row["resultado_esperado"]
    if expected == "CONFIRMED":
        assert order.confirm(customer_debt=debt) == pytest.approx(float(row["cobro_esperado"]))
        assert order.status == "CONFIRMED"
    else:
        with pytest.raises(EXCEPTIONS[expected]):
            order.confirm(customer_debt=debt)
