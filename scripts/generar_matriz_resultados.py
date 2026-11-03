"""Genera docs/matriz_resultados.csv: resultado esperado vs resultado real de cada caso."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.domain import Order  # noqa: E402


def run_case(row):
    order = Order(float(row["total"]), vip=row["vip"] == "1", status=row["estado_inicial"])
    try:
        charged = order.confirm(customer_debt=float(row["deuda"]))
    except Exception as exc:  # se registra el tipo de excepcion real
        return type(exc).__name__, ""
    return "CONFIRMED", f"{charged:.2f}"


def main():
    src = ROOT / "data" / "matriz_pruebas.csv"
    out = ROOT / "docs" / "matriz_resultados.csv"
    with src.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = ["caso_id", "regla", "tipo", "resultado_esperado", "cobro_esperado",
              "resultado_real", "cobro_real", "estado"]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            real, charged = run_case(row)
            ok = real == row["resultado_esperado"] and (
                not row["cobro_esperado"] or abs(float(charged) - float(row["cobro_esperado"])) < 0.005
            )
            writer.writerow({
                "caso_id": row["caso_id"], "regla": row["regla"], "tipo": row["tipo"],
                "resultado_esperado": row["resultado_esperado"],
                "cobro_esperado": row["cobro_esperado"],
                "resultado_real": real, "cobro_real": charged,
                "estado": "PASA" if ok else "FALLA",
            })
    print(f"Matriz escrita en {out}")


if __name__ == "__main__":
    main()
