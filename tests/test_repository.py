from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain import Order
from src.repository import OrderRow, SqlOrderRepository, make_engine


def test_repository_commit():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.commit()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)).total == 120


def test_repository_rollback():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(1, Order(120))
        session.rollback()
        assert session.scalar(select(OrderRow).where(OrderRow.id == 1)) is None


def test_repository_commit_order_250():
    engine = make_engine()
    with Session(engine) as session:
        SqlOrderRepository(session).save(2, Order(250))
        session.commit()
        row = session.scalar(select(OrderRow).where(OrderRow.id == 2))
        assert (row.id, row.total, row.status) == (2, 250, "NEW")


def test_repository_persists_confirmed_status():
    engine = make_engine()
    order = Order(200, vip=True)
    order.confirm()
    with Session(engine) as session:
        SqlOrderRepository(session).save(3, order)
        session.commit()
    with Session(engine) as other_session:  # sesión distinta: el dato sí quedó guardado
        row = other_session.get(OrderRow, 3)
        assert row.status == "CONFIRMED"


def test_rollback_discards_only_uncommitted_work():
    engine = make_engine()
    with Session(engine) as session:
        repo = SqlOrderRepository(session)
        repo.save(1, Order(100))
        session.commit()
        repo.save(2, Order(200))
        session.rollback()
        assert session.get(OrderRow, 1) is not None
        assert session.get(OrderRow, 2) is None


def test_unique_id_is_enforced():
    engine = make_engine()
    with Session(engine) as first:
        SqlOrderRepository(first).save(1, Order(120))
        first.commit()
    with Session(engine) as second:
        SqlOrderRepository(second).save(1, Order(999))
        with pytest.raises(IntegrityError):
            second.commit()
        second.rollback()
    with Session(engine) as check:
        assert check.get(OrderRow, 1).total == 120  # el original no cambió


def test_total_is_not_nullable():
    engine = make_engine()
    with Session(engine) as session:
        session.add(OrderRow(id=5, total=None, status="NEW"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_each_engine_is_isolated():
    with Session(make_engine()) as a:
        SqlOrderRepository(a).save(1, Order(10))
        a.commit()
    with Session(make_engine()) as b:  # otro motor en memoria = otra base vacía
        assert b.get(OrderRow, 1) is None


def test_domain_does_not_import_orm():
    source = (Path(__file__).resolve().parent.parent / "src" / "domain.py").read_text("utf-8")
    assert "sqlalchemy" not in source.lower()
