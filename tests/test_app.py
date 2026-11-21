"""Automated tests for Desi Bites menu, config, order logic, LangGraph, and Streamlit UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from backend.config import MissingConfigError, get_gemini_config
from backend.graph import IntentAnalysis, ExtractedOrderItem, run_assistant_turn
from backend.order_service import (
    DELIVERY_FEE_INR,
    FREE_DELIVERY_THRESHOLD_INR,
    add_to_cart,
    calculate_order_totals,
    create_demo_order,
    remove_from_cart,
    update_cart_quantity,
)
from data.menu import (
    CATEGORIES,
    find_menu_item,
    format_menu_for_llm,
    get_all_menu_items,
    get_featured_items,
    get_menu_by_dietary,
    get_todays_specials,
    search_menu,
)


def test_menu_categories_and_dietary_coverage() -> None:
    items = get_all_menu_items()
    assert len(items) >= 25
    present_categories = {item.category for item in items}
    assert set(CATEGORIES) == present_categories

    veg = get_menu_by_dietary("Veg")
    nonveg = get_menu_by_dietary("Non-Veg")
    assert len(veg) > 0
    assert len(nonveg) > 0
    assert all(item.price_inr > 0 for item in items)
    assert len(get_featured_items()) > 0
    assert len(get_todays_specials()) > 0


def test_menu_search_and_fuzzy_lookup() -> None:
    paneer_results = search_menu(query="paneer", dietary="Veg")
    assert len(paneer_results) >= 2
    assert all(i.dietary == "Veg" for i in paneer_results)

    matched = find_menu_item("butter chicken")
    assert matched is not None
    assert matched.name == "Old Delhi Butter Chicken"

    assert find_menu_item("pepperoni pizza") is None
    catalog_str = format_menu_for_llm()
    assert "Old Delhi Butter Chicken" in catalog_str
    assert "₹379" in catalog_str


def test_cart_calculations_and_demo_order() -> None:
    cart: list[dict[str, Any]] = []
    # Add 1x Garlic Butter Naan (₹79)
    cart, _, err = add_to_cart(cart, "veg-garlic-butter-naan", quantity=2)
    assert err is None
    assert len(cart) == 1
    assert cart[0]["quantity"] == 2

    # Same item + customization merges quantity
    cart, _, err = add_to_cart(cart, "Garlic Butter Naan", quantity=1)
    assert err is None
    assert len(cart) == 1
    assert cart[0]["quantity"] == 3

    totals = calculate_order_totals(cart, order_type="Delivery")
    assert totals["subtotal_inr"] == 79 * 3
    assert totals["delivery_fee_inr"] == DELIVERY_FEE_INR
    assert totals["total_inr"] == 79 * 3 + DELIVERY_FEE_INR

    # Pickup has zero delivery fee
    pickup_totals = calculate_order_totals(cart, order_type="Pickup")
    assert pickup_totals["delivery_fee_inr"] == 0
    assert pickup_totals["total_inr"] == 79 * 3

    # Exceeding free delivery threshold waives fee
    cart, _, err = add_to_cart(cart, "nonveg-hyderabadi-chicken-biryani", quantity=2, spice_level="Spicy")
    assert err is None
    high_totals = calculate_order_totals(cart, order_type="Delivery")
    assert high_totals["subtotal_inr"] >= FREE_DELIVERY_THRESHOLD_INR
    assert high_totals["delivery_fee_inr"] == 0

    # Update & remove
    cid = cart[0]["cart_item_id"]
    cart = update_cart_quantity(cart, cid, 1)
    assert cart[0]["quantity"] == 1
    cart = remove_from_cart(cart, cid)
    assert len(cart) == 1

    # Validation refuses incomplete customer details
    order, err = create_demo_order(cart, {"name": "", "phone": "123", "address": "", "order_type": "Delivery"})
    assert order is None
    assert err is not None

    # Valid demo order succeeds
    order, err = create_demo_order(
        cart,
        {
            "name": "Aarav Sharma",
            "phone": "9876543210",
            "address": "42 MG Road, Bengaluru",
            "order_type": "Delivery",
        },
    )
    assert err is None
    assert order is not None
    assert order["order_id"].startswith("DB-")
    assert order["is_demo"] is True
    assert order["status"] == "Confirmed (Demo Order)"


def test_missing_api_key_raises_clean_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(MissingConfigError):
        get_gemini_config()

    monkeypatch.setenv("GEMINI_API_KEY", "MY_GEMINI_API_KEY")
    with pytest.raises(MissingConfigError):
        get_gemini_config()


@dataclass
class _FakeStructuredLLM:
    analysis: IntentAnalysis

    def invoke(self, _messages: Any) -> IntentAnalysis:
        return self.analysis


@dataclass
class _FakeMessage:
    content: str


class _FakeLLM:
    def __init__(self, analysis: IntentAnalysis, reply_text: str) -> None:
        self._analysis = analysis
        self._reply_text = reply_text

    def with_structured_output(self, _schema: Any) -> _FakeStructuredLLM:
        return _FakeStructuredLLM(self._analysis)

    def invoke(self, _messages: Any) -> _FakeMessage:
        return _FakeMessage(content=self._reply_text)


def test_langgraph_order_and_confirmation_flow() -> None:
    # Step 1: Customer asks to add Butter Chicken & an invalid item ("Sushi")
    add_analysis = IntentAnalysis(
        intent="order_request",
        search_keywords=["Butter Chicken"],
        dietary_filter="All",
        items=[
            ExtractedOrderItem(dish_name="Butter Chicken", quantity=2, spice_level="Medium"),
            ExtractedOrderItem(dish_name="Dragon Sushi Roll", quantity=1),
        ],
    )
    res1 = run_assistant_turn(
        user_message="Add 2 medium Butter Chicken and 1 Dragon Sushi Roll",
        chat_history=[],
        current_cart=[],
        customer_details={"name": "", "phone": "", "address": "", "order_type": "Delivery"},
        llm_factory=lambda _t: _FakeLLM(add_analysis, "Added 2x Old Delhi Butter Chicken; Sushi is unavailable."),
    )
    assert res1["error"] is None
    assert len(res1["working_cart"]) == 1
    assert res1["working_cart"][0]["name"] == "Old Delhi Butter Chicken"
    assert res1["working_cart"][0]["quantity"] == 2
    assert res1["unavailable_items"] == ["Dragon Sushi Roll"]
    assert res1["order_confirmed"] is False

    # Step 2: Customer tries to confirm without customer details -> MUST NOT confirm
    premature_confirm = IntentAnalysis(
        intent="confirm_order",
        explicit_confirmation=True,
    )
    res2 = run_assistant_turn(
        user_message="Confirm my order now",
        chat_history=[],
        current_cart=res1["working_cart"],
        customer_details=res1["customer_details"],
        llm_factory=lambda _t: _FakeLLM(premature_confirm, "Please share your name, phone, and address first."),
    )
    assert res2["order_confirmed"] is False
    assert res2["confirmed_order"] is None
    assert "Full Name" in res2["missing_details"]

    # Step 3: Customer provides details and confirms -> MUST confirm demo order
    final_confirm = IntentAnalysis(
        intent="confirm_order",
        explicit_confirmation=True,
        customer_name="Priya Nair",
        customer_phone="9876543210",
        customer_address="18 Indiranagar, Bengaluru",
        order_type="Delivery",
    )
    res3 = run_assistant_turn(
        user_message="Name Priya Nair, phone 9876543210, address 18 Indiranagar Bengaluru. Confirm order!",
        chat_history=[],
        current_cart=res1["working_cart"],
        customer_details=res1["customer_details"],
        llm_factory=lambda _t: _FakeLLM(final_confirm, "Demo order confirmed!"),
    )
    assert res3["order_confirmed"] is True
    assert res3["confirmed_order"] is not None
    assert res3["confirmed_order"]["order_id"].startswith("DB-")
    assert res3["working_cart"] == []


def test_streamlit_app_renders_cleanly() -> None:
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15)
    at.run()
    assert not at.exception

    # Navigate to Menu
    at.button(key="nav_Menu").click().run()
    assert not at.exception
    assert at.session_state["active_section"] == "Menu"

    # Quick-add a Vegetarian dish from Menu
    at.button(key="menu_veg_quick_veg-paneer-tikka-angara").click().run()
    assert not at.exception
    assert len(at.session_state["cart"]) == 1

    # Navigate to AI Order Assistant
    at.button(key="nav_AI Order Assistant").click().run()
    assert not at.exception
    assert at.session_state["active_section"] == "AI Order Assistant"

    # Navigate to Cart & Checkout and verify cart persisted across sections
    at.button(key="nav_Cart & Checkout").click().run()
    assert not at.exception
    assert at.session_state["active_section"] == "Cart & Checkout"
    assert len(at.session_state["cart"]) == 1

    # Fill customer details and submit demo order
    at.text_input[0].input("Aarav Sharma").run()
    at.text_input[1].input("9876543210").run()
    at.text_area[0].input("42 MG Road, Bengaluru").run()
    at.button(key="submit_demo_order_btn").click().run()
    assert not at.exception
    assert at.session_state["active_section"] == "Order Confirmation"
    assert at.session_state["cart"] == []
    assert at.session_state["latest_order"] is not None
    assert at.session_state["latest_order"]["order_id"].startswith("DB-")
