"""Pure Python cart, pricing, validation, and demo order service for Desi Bites."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import uuid4

from data.menu import SPICE_LEVELS, MenuItem, find_menu_item, get_menu_item_by_id

FREE_DELIVERY_THRESHOLD_INR = 599
DELIVERY_FEE_INR = 40
ORDER_TYPES = ("Delivery", "Pickup")


def build_cart_item_id(
    item_id: str,
    spice_level: str,
    customizations: list[str],
    special_instructions: str,
) -> str:
    """Create a deterministic key so identical dish configurations merge quantities."""
    normalized_customs = ",".join(sorted(c.strip().lower() for c in customizations if c.strip()))
    normalized_notes = special_instructions.strip().lower()
    raw = f"{item_id}|{spice_level.strip().lower()}|{normalized_customs}|{normalized_notes}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{item_id}__{digest}"


def _resolve_item(item_identifier: str) -> MenuItem | None:
    return get_menu_item_by_id(item_identifier) or find_menu_item(item_identifier)


def add_to_cart(
    cart: list[dict[str, Any]],
    item_identifier: str,
    quantity: int = 1,
    spice_level: str | None = None,
    customizations: list[str] | None = None,
    special_instructions: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str | None]:
    """Validate against the local menu and add or merge an item into a new cart list."""
    menu_item = _resolve_item(item_identifier)
    if menu_item is None:
        return deepcopy(cart), None, f"Dish '{item_identifier}' was not found on the Desi Bites menu."

    if quantity < 1:
        return deepcopy(cart), None, "Quantity must be at least 1."

    chosen_spice = menu_item.spice_level
    if spice_level and menu_item.customizable_spice:
        candidate = spice_level.strip().title()
        if candidate in SPICE_LEVELS:
            chosen_spice = candidate

    clean_customizations: list[str] = []
    if customizations:
        allowed_lookup = {c.lower(): c for c in menu_item.customizations}
        for c in customizations:
            c_clean = c.strip()
            if not c_clean:
                continue
            matched = allowed_lookup.get(c_clean.lower())
            if matched:
                if matched not in clean_customizations:
                    clean_customizations.append(matched)
            else:
                # Preserve short explicit customer preference inside special instructions if not an exact preset
                if c_clean not in clean_customizations:
                    clean_customizations.append(c_clean)

    notes_clean = special_instructions.strip()
    cart_item_id = build_cart_item_id(menu_item.id, chosen_spice, clean_customizations, notes_clean)

    updated_cart = deepcopy(cart)
    for existing in updated_cart:
        if existing["cart_item_id"] == cart_item_id:
            existing["quantity"] += int(quantity)
            return updated_cart, existing, None

    new_entry: dict[str, Any] = {
        "cart_item_id": cart_item_id,
        "item_id": menu_item.id,
        "name": menu_item.name,
        "dietary": menu_item.dietary,
        "category": menu_item.category,
        "unit_price_inr": menu_item.price_inr,
        "quantity": int(quantity),
        "spice_level": chosen_spice,
        "customizations": clean_customizations,
        "special_instructions": notes_clean,
    }
    updated_cart.append(new_entry)
    return updated_cart, new_entry, None


def update_cart_quantity(
    cart: list[dict[str, Any]],
    cart_item_id: str,
    new_quantity: int,
) -> list[dict[str, Any]]:
    """Update item quantity or remove if new_quantity <= 0."""
    updated_cart: list[dict[str, Any]] = []
    for entry in deepcopy(cart):
        if entry["cart_item_id"] == cart_item_id:
            if new_quantity > 0:
                entry["quantity"] = int(new_quantity)
                updated_cart.append(entry)
        else:
            updated_cart.append(entry)
    return updated_cart


def remove_from_cart(cart: list[dict[str, Any]], cart_item_id: str) -> list[dict[str, Any]]:
    """Remove an item from the cart by its cart_item_id."""
    return [deepcopy(entry) for entry in cart if entry["cart_item_id"] != cart_item_id]


def remove_by_dish_name(cart: list[dict[str, Any]], item_identifier: str) -> tuple[list[dict[str, Any]], bool]:
    """Remove any cart lines matching a menu item ID or name."""
    menu_item = _resolve_item(item_identifier)
    if menu_item is None:
        return deepcopy(cart), False
    filtered = [deepcopy(entry) for entry in cart if entry["item_id"] != menu_item.id]
    return filtered, len(filtered) != len(cart)


def clear_cart() -> list[dict[str, Any]]:
    """Return an empty cart."""
    return []


def calculate_order_totals(cart: list[dict[str, Any]], order_type: str = "Delivery") -> dict[str, int]:
    """Calculate authoritative INR subtotal, delivery fee, and total."""
    item_count = sum(int(item["quantity"]) for item in cart)
    subtotal_inr = sum(int(item["unit_price_inr"]) * int(item["quantity"]) for item in cart)

    if not cart or order_type == "Pickup" or subtotal_inr >= FREE_DELIVERY_THRESHOLD_INR:
        delivery_fee_inr = 0
    else:
        delivery_fee_inr = DELIVERY_FEE_INR

    free_delivery_remaining_inr = (
        max(0, FREE_DELIVERY_THRESHOLD_INR - subtotal_inr)
        if cart and order_type == "Delivery" and subtotal_inr < FREE_DELIVERY_THRESHOLD_INR
        else 0
    )

    total_inr = subtotal_inr + delivery_fee_inr
    return {
        "item_count": item_count,
        "subtotal_inr": subtotal_inr,
        "delivery_fee_inr": delivery_fee_inr,
        "free_delivery_remaining_inr": free_delivery_remaining_inr,
        "total_inr": total_inr,
    }


def validate_customer_details(
    customer_details: dict[str, str] | None,
    order_type: str = "Delivery",
) -> list[str]:
    """Return a list of missing or incomplete required customer fields."""
    details = customer_details or {}
    missing: list[str] = []

    if not details.get("name", "").strip():
        missing.append("Full Name")

    phone = details.get("phone", "").strip()
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 10:
        missing.append("10-digit Phone Number")

    if order_type == "Delivery" and not details.get("address", "").strip():
        missing.append("Delivery Address")

    return missing


def create_demo_order(
    cart: list[dict[str, Any]],
    customer_details: dict[str, str],
) -> tuple[dict[str, Any] | None, str | None]:
    """Create a validated demo order record (no real payment or delivery API)."""
    if not cart:
        return None, "Your cart is empty. Please add at least one dish before placing an order."

    order_type = customer_details.get("order_type", "Delivery").strip() or "Delivery"
    if order_type not in ORDER_TYPES:
        order_type = "Delivery"

    missing_fields = validate_customer_details(customer_details, order_type=order_type)
    if missing_fields:
        return None, f"Missing required customer details: {', '.join(missing_fields)}."

    totals = calculate_order_totals(cart, order_type=order_type)
    now = datetime.now()
    order_id = f"DB-{now.strftime('%y%m%d')}-{uuid4().hex[:4].upper()}"

    order_record: dict[str, Any] = {
        "order_id": order_id,
        "created_at": now.strftime("%d %b %Y, %I:%M %p"),
        "status": "Confirmed (Demo Order)",
        "is_demo": True,
        "order_type": order_type,
        "items": deepcopy(cart),
        "totals": totals,
        "customer": {
            "name": customer_details.get("name", "").strip(),
            "phone": customer_details.get("phone", "").strip(),
            "address": customer_details.get("address", "").strip() if order_type == "Delivery" else "Self Pickup at Desi Bites Kitchen",
            "notes": customer_details.get("notes", "").strip(),
        },
        "payment_method": "Pay on Delivery / Counter (Demo)",
        "disclaimer": "Demo Order Only — no real payment or live delivery dispatch was triggered.",
    }
    return order_record, None


def format_cart_summary(cart: list[dict[str, Any]], order_type: str = "Delivery") -> str:
    """Format the live cart into readable text for Gemini context."""
    if not cart:
        return "Cart is currently empty."

    lines: list[str] = []
    for idx, item in enumerate(cart, start=1):
        line_total = item["unit_price_inr"] * item["quantity"]
        extras: list[str] = [f"Spice: {item['spice_level']}"]
        if item.get("customizations"):
            extras.append(f"Customizations: {', '.join(item['customizations'])}")
        if item.get("special_instructions"):
            extras.append(f"Note: {item['special_instructions']}")
        lines.append(
            f"{idx}. {item['quantity']}x {item['name']} (₹{item['unit_price_inr']} each = ₹{line_total}) "
            f"[{'; '.join(extras)}]"
        )

    totals = calculate_order_totals(cart, order_type=order_type)
    lines.append(
        f"Summary ({order_type}): Subtotal ₹{totals['subtotal_inr']}, "
        f"Delivery Fee ₹{totals['delivery_fee_inr']}, Total ₹{totals['total_inr']}"
    )
    return "\n".join(lines)
