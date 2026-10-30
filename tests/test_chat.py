import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.chat import UNKNOWN_RESPONSE, ask


@pytest.mark.parametrize(
    ("route_name", "module_name"),
    [
        ("faq", "faq"),
        ("sql", "sql"),
        ("small_talk", "small_talk"),
    ],
)
def test_ask_dispatches_to_selected_chain(monkeypatch, route_name, module_name):
    query = "sample customer question"
    calls = []
    routed_queries = []

    def chain(received_query):
        calls.append(received_query)
        return f"{route_name} answer"

    router_module = ModuleType("router")
    def fake_router(received_query):
        routed_queries.append(received_query)
        return SimpleNamespace(name=route_name)

    router_module.router = fake_router

    # Stub all imported integrations so this test never initializes models or APIs.
    for name, function in (("faq", "faq_chain"), ("sql", "sql_chain"), ("small_talk", "talk")):
        module = ModuleType(name)
        setattr(module, function, chain if name == module_name else lambda _: "unused")
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setitem(sys.modules, "router", router_module)

    assert ask(query) == (f"{route_name} answer", route_name)
    assert calls == [query]
    assert routed_queries == [query]


def test_ask_returns_fallback_for_unrecognized_route(monkeypatch):
    router_module = ModuleType("router")
    router_module.router = lambda _: SimpleNamespace(name="other")
    monkeypatch.setitem(sys.modules, "router", router_module)

    for name, function in (("faq", "faq_chain"), ("sql", "sql_chain"), ("small_talk", "talk")):
        module = ModuleType(name)
        setattr(module, function, lambda _: pytest.fail("No chain should run"))
        monkeypatch.setitem(sys.modules, name, module)

    assert ask("unmatched question") == (UNKNOWN_RESPONSE, "unknown")


@pytest.mark.parametrize("query", ["", "   ", "  return policy?  "])
def test_ask_passes_query_to_router_without_modifying_it(monkeypatch, query):
    received = []
    router_module = ModuleType("router")

    def fake_router(value):
        received.append(value)
        return SimpleNamespace(name="faq")

    router_module.router = fake_router
    monkeypatch.setitem(sys.modules, "router", router_module)

    faq_module = ModuleType("faq")
    faq_module.faq_chain = lambda value: value
    monkeypatch.setitem(sys.modules, "faq", faq_module)
    sql_module = ModuleType("sql")
    sql_module.sql_chain = lambda _: pytest.fail("SQL chain should not run")
    monkeypatch.setitem(sys.modules, "sql", sql_module)
    talk_module = ModuleType("small_talk")
    talk_module.talk = lambda _: pytest.fail("Small-talk chain should not run")
    monkeypatch.setitem(sys.modules, "small_talk", talk_module)

    assert ask(query) == (query, "faq")
    assert received == [query]
