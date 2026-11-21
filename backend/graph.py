"""LangGraph workflow for the Desi Bites AI Order Assistant."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from backend.gemini_client import format_gemini_error, get_gemini_llm
from backend.order_service import (
    add_to_cart,
    calculate_order_totals,
    clear_cart,
    create_demo_order,
    format_cart_summary,
    remove_by_dish_name,
    validate_customer_details,
)
from data.menu import (
    find_menu_item,
    format_menu_for_llm,
    get_all_menu_items,
    search_menu,
)


class ExtractedOrderItem(BaseModel):
    """Structured representation of a dish mentioned by the customer."""

    dish_name: str = Field(description="Dish name as stated or matched to the Desi Bites menu.")
    quantity: int = Field(default=1, ge=1, description="Number of units requested.")
    spice_level: Literal["", "Mild", "Medium", "Spicy"] = Field(
        default="",
        description="Explicit spice preference if mentioned, else empty string.",
    )
    customizations: list[str] = Field(
        default_factory=list,
        description="Any dish customizations requested (e.g., Extra Garlic, Less Butter, Boneless).",
    )
    special_instructions: str = Field(
        default="",
        description="Any additional cooking or allergy note for this dish.",
    )


class IntentAnalysis(BaseModel):
    """Structured intent and entity extraction from customer chat message."""

    intent: Literal[
        "menu_inquiry",
        "order_request",
        "remove_item",
        "provide_details",
        "confirm_order",
        "cart_review",
        "general_chat",
    ] = Field(description="Primary customer intent for this turn.")
    search_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords, dish names, ingredients, or categories to look up in the menu.",
    )
    dietary_filter: Literal["All", "Veg", "Non-Veg"] = Field(
        default="All",
        description="Dietary preference if specified.",
    )
    items: list[ExtractedOrderItem] = Field(
        default_factory=list,
        description="Dishes the customer wants to add or order right now.",
    )
    remove_dish_names: list[str] = Field(
        default_factory=list,
        description="Dishes the customer explicitly asked to remove from the cart.",
    )
    customer_name: str = Field(default="", description="Customer full name if provided.")
    customer_phone: str = Field(default="", description="Customer phone number if provided.")
    customer_address: str = Field(default="", description="Delivery address if provided.")
    order_type: Literal["", "Delivery", "Pickup"] = Field(
        default="",
        description="Delivery or Pickup if stated by customer.",
    )
    explicit_confirmation: bool = Field(
        default=False,
        description=(
            "True ONLY if the customer explicitly confirms submitting/placing their final order "
            "(e.g., 'yes, confirm order', 'place my order now')."
        ),
    )


class AssistantState(TypedDict):
    """Typed state flowing through the Desi Bites LangGraph nodes."""

    user_message: str
    chat_history: list[dict[str, str]]
    current_cart: list[dict[str, Any]]
    working_cart: list[dict[str, Any]]
    customer_details: dict[str, str]
    intent: str
    explicit_confirmation: bool
    search_keywords: list[str]
    dietary_filter: str
    extracted_items: list[dict[str, Any]]
    remove_dish_names: list[str]
    validated_items: list[dict[str, Any]]
    unavailable_items: list[str]
    retrieved_menu_context: str
    missing_details: list[str]
    spice_clarifications: list[str]
    cart_actions: list[dict[str, Any]]
    order_confirmed: bool
    confirmed_order: dict[str, Any] | None
    assistant_reply: str
    error: str | None


def _format_history_snippet(chat_history: list[dict[str, str]], limit: int = 8) -> str:
    if not chat_history:
        return "No prior conversation."
    recent = chat_history[-limit:]
    return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in recent)


def build_ordering_graph(llm_factory: Callable[[float], Any] | None = None):
    """Build and compile the Desi Bites LangGraph workflow."""
    make_llm = llm_factory or (lambda temp: get_gemini_llm(temperature=temp))

    def understand_intent(state: AssistantState) -> dict[str, Any]:
        """Classify customer intent and extract order entities using Gemini."""
        try:
            llm = make_llm(0.1)
            structured_llm = llm.with_structured_output(IntentAnalysis)

            menu_brief = "\n".join(
                f"- {item.name} ({item.dietary}, {item.category}, ₹{item.price_inr})"
                for item in get_all_menu_items()
            )
            order_type = state["customer_details"].get("order_type", "Delivery") or "Delivery"
            cart_text = format_cart_summary(state["current_cart"], order_type=order_type)
            history_text = _format_history_snippet(state["chat_history"])
            details = state["customer_details"]

            system_prompt = (
                "You are the intent and order-extraction engine for Desi Bites, a modern Indian restaurant.\n"
                "Analyze the customer's latest message in the context of recent conversation, current cart, "
                "and known customer details.\n\n"
                "Rules:\n"
                "1. Only extract dishes that the customer wants to add/order NOW in `items`.\n"
                "2. If they ask about ingredients, prices, spice levels, or recommendations without ordering, "
                "set intent='menu_inquiry'.\n"
                "3. Set intent='confirm_order' and explicit_confirmation=True ONLY when the customer "
                "explicitly asks to finalize/submit/confirm the order (e.g., 'yes place the order', 'confirm my order').\n"
                "4. If the user provides their name, phone, or address, capture those fields cleanly.\n"
                "5. Do NOT invent menu items; preserve what the customer asked for in `dish_name`.\n\n"
                f"MENU REFERENCE:\n{menu_brief}\n\n"
                f"CURRENT CART:\n{cart_text}\n\n"
                f"KNOWN CUSTOMER DETAILS: name={details.get('name', '')!r}, "
                f"phone={details.get('phone', '')!r}, address={details.get('address', '')!r}, "
                f"order_type={order_type!r}"
            )

            analysis: IntentAnalysis = structured_llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(
                        content=f"CONVERSATION HISTORY:\n{history_text}\n\nLATEST MESSAGE:\n{state['user_message']}"
                    ),
                ]
            )

            merged_details = dict(state["customer_details"])
            if analysis.customer_name.strip():
                merged_details["name"] = analysis.customer_name.strip()
            if analysis.customer_phone.strip():
                merged_details["phone"] = analysis.customer_phone.strip()
            if analysis.customer_address.strip():
                merged_details["address"] = analysis.customer_address.strip()
            if analysis.order_type:
                merged_details["order_type"] = analysis.order_type
            elif not merged_details.get("order_type"):
                merged_details["order_type"] = "Delivery"

            return {
                "intent": analysis.intent,
                "explicit_confirmation": bool(analysis.explicit_confirmation),
                "search_keywords": analysis.search_keywords,
                "dietary_filter": analysis.dietary_filter,
                "extracted_items": [item.model_dump() for item in analysis.items],
                "remove_dish_names": analysis.remove_dish_names,
                "customer_details": merged_details,
                "working_cart": deepcopy(state["current_cart"]),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "error": format_gemini_error(exc),
                "assistant_reply": format_gemini_error(exc),
            }

    def retrieve_menu_info(state: AssistantState) -> dict[str, Any]:
        """Retrieve authoritative dish facts from local data/menu.py and validate items."""
        if state.get("error"):
            return {}

        dietary = state.get("dietary_filter", "All")
        keywords = state.get("search_keywords", [])

        matched_items = []
        seen_ids: set[str] = set()
        for kw in keywords:
            for item in search_menu(query=kw, dietary=dietary):
                if item.id not in seen_ids:
                    matched_items.append(item)
                    seen_ids.add(item.id)

        # Validate extracted items against the true local menu
        validated_items: list[dict[str, Any]] = []
        unavailable_items: list[str] = []

        for req in state.get("extracted_items", []):
            dish_query = str(req.get("dish_name", "")).strip()
            resolved = find_menu_item(dish_query)
            if resolved is None:
                if dish_query:
                    unavailable_items.append(dish_query)
                continue

            if resolved.id not in seen_ids:
                matched_items.append(resolved)
                seen_ids.add(resolved.id)

            validated_items.append(
                {
                    "item_id": resolved.id,
                    "name": resolved.name,
                    "quantity": max(1, int(req.get("quantity", 1))),
                    "spice_level": req.get("spice_level", "") or "",
                    "customizable_spice": resolved.customizable_spice,
                    "default_spice": resolved.spice_level,
                    "customizations": list(req.get("customizations") or []),
                    "special_instructions": str(req.get("special_instructions") or "").strip(),
                }
            )

        # Provide complete authoritative catalog when inquiry is broad or no narrow match was found
        if not matched_items or state.get("intent") in ("menu_inquiry", "general_chat"):
            catalog_items = (
                search_menu(dietary=dietary) if dietary in ("Veg", "Non-Veg") else get_all_menu_items()
            )
        else:
            catalog_items = matched_items

        return {
            "validated_items": validated_items,
            "unavailable_items": unavailable_items,
            "retrieved_menu_context": format_menu_for_llm(catalog_items),
        }

    def collect_missing_details(state: AssistantState) -> dict[str, Any]:
        """Check for missing spice preferences on new items and missing checkout details."""
        if state.get("error"):
            return {}

        spice_clarifications: list[str] = []
        for item in state.get("validated_items", []):
            if item["customizable_spice"] and not item["spice_level"]:
                spice_clarifications.append(
                    f"{item['name']} (currently set to restaurant default: {item['default_spice']}; "
                    f"can be Mild, Medium, or Spicy)"
                )

        order_type = state["customer_details"].get("order_type", "Delivery") or "Delivery"
        missing_customer_fields = validate_customer_details(
            state["customer_details"],
            order_type=order_type,
        )

        return {
            "spice_clarifications": spice_clarifications,
            "missing_details": missing_customer_fields,
        }

    def prepare_cart_update(state: AssistantState) -> dict[str, Any]:
        """Apply validated item additions/removals to the working cart (does NOT submit order)."""
        if state.get("error"):
            return {}

        working = deepcopy(state["working_cart"])
        actions: list[dict[str, Any]] = []

        for dish_name in state.get("remove_dish_names", []):
            working, removed = remove_by_dish_name(working, dish_name)
            if removed:
                actions.append({"action": "remove", "dish_name": dish_name})

        for req in state.get("validated_items", []):
            chosen_spice = req["spice_level"] or req["default_spice"]
            working, entry, err = add_to_cart(
                working,
                item_identifier=req["item_id"],
                quantity=req["quantity"],
                spice_level=chosen_spice,
                customizations=req["customizations"],
                special_instructions=req["special_instructions"],
            )
            if entry and not err:
                actions.append(
                    {
                        "action": "add",
                        "item_id": entry["item_id"],
                        "name": entry["name"],
                        "quantity": req["quantity"],
                        "spice_level": entry["spice_level"],
                        "customizations": entry["customizations"],
                    }
                )

        return {
            "working_cart": working,
            "cart_actions": actions,
        }

    def confirm_order(state: AssistantState) -> dict[str, Any]:
        """Submit a demo order ONLY when explicitly confirmed, cart is non-empty, and details are valid."""
        if state.get("error"):
            return {}

        working = deepcopy(state["working_cart"])
        if not working:
            return {
                "order_confirmed": False,
                "confirmed_order": None,
                "missing_details": ["At least one dish in your cart"],
            }

        if not state.get("explicit_confirmation", False):
            return {
                "order_confirmed": False,
                "confirmed_order": None,
            }

        order_type = state["customer_details"].get("order_type", "Delivery") or "Delivery"
        missing_fields = validate_customer_details(state["customer_details"], order_type=order_type)
        if missing_fields:
            return {
                "order_confirmed": False,
                "confirmed_order": None,
                "missing_details": missing_fields,
            }

        order_record, err = create_demo_order(working, state["customer_details"])
        if err or order_record is None:
            return {
                "order_confirmed": False,
                "confirmed_order": None,
                "missing_details": [err or "Unable to validate demo order."],
            }

        return {
            "order_confirmed": True,
            "confirmed_order": order_record,
            "working_cart": clear_cart(),
            "cart_actions": [*state.get("cart_actions", []), {"action": "clear"}],
            "missing_details": [],
        }

    def generate_response(state: AssistantState) -> dict[str, Any]:
        """Generate the final grounded hospitality reply using Gemini."""
        if state.get("error"):
            return {"assistant_reply": state["error"]}

        try:
            llm = make_llm(0.3)
            order_type = state["customer_details"].get("order_type", "Delivery") or "Delivery"
            cart_summary = format_cart_summary(state["working_cart"], order_type=order_type)
            totals = calculate_order_totals(state["working_cart"], order_type=order_type)
            history_text = _format_history_snippet(state["chat_history"])

            actions_text = (
                ", ".join(
                    f"{a['action']} {a.get('quantity', '')}x {a.get('name', a.get('dish_name', ''))}".strip()
                    for a in state.get("cart_actions", [])
                )
                or "None"
            )
            unavailable_text = ", ".join(state.get("unavailable_items", [])) or "None"
            spice_notes = "; ".join(state.get("spice_clarifications", [])) or "None"
            missing_text = ", ".join(state.get("missing_details", [])) or "None"

            confirmed_text = "Not confirmed yet."
            if state.get("order_confirmed") and state.get("confirmed_order"):
                order = state["confirmed_order"]
                confirmed_text = (
                    f"CONFIRMED DEMO ORDER: Order ID {order['order_id']}, "
                    f"Total ₹{order['totals']['total_inr']}, Type: {order['order_type']}, "
                    f"Customer: {order['customer']['name']} ({order['customer']['phone']}). "
                    f"{order['disclaimer']}"
                )

            system_prompt = (
                "You are the warm, attentive AI Order Assistant for DESI BITES, a modern Indian restaurant.\n"
                "CRITICAL GROUNDING RULES:\n"
                "1. Use ONLY the MENU SOURCE OF TRUTH below for dish names, dietary labels (Veg/Non-Veg), "
                "prices (in ₹ INR), ingredients, spice levels, and customizations. NEVER invent dishes or prices.\n"
                "2. If `UNAVAILABLE ITEMS` is not None, politely say Desi Bites does not serve those items and "
                "suggest 2-3 close real items from the menu.\n"
                "3. NEVER claim an order has been placed or confirmed unless `ORDER STATUS` starts with "
                "'CONFIRMED DEMO ORDER'.\n"
                "4. When items were added to the cart, clearly list what is now in the cart with subtotal, "
                "delivery fee (free over ₹599 or on Pickup, else ₹40), and total ₹"
                f"{totals['total_inr']}.\n"
                "5. If `SPICE CLARIFICATIONS` is not None, let the guest know their dish was added with its "
                "default spice level and ask if they'd like to adjust spice (Mild/Medium/Spicy) or add breads/drinks.\n"
                "6. If `MISSING CUSTOMER DETAILS` is not None and the cart has items, politely ask for those "
                "missing details (e.g., Full Name, 10-digit Phone Number, Delivery Address or Pickup preference) "
                "and remind them to reply 'Confirm order' when ready to submit their demo order.\n"
                "7. Keep responses concise, structured with clean bullet points, and easy to read on mobile.\n\n"
                f"MENU SOURCE OF TRUTH:\n{state['retrieved_menu_context']}\n\n"
                f"CART ACTIONS APPLIED THIS TURN: {actions_text}\n"
                f"UNAVAILABLE ITEMS: {unavailable_text}\n"
                f"SPICE CLARIFICATIONS: {spice_notes}\n"
                f"CURRENT WORKING CART:\n{cart_summary}\n\n"
                f"CUSTOMER DETAILS SO FAR: {state['customer_details']}\n"
                f"MISSING CUSTOMER DETAILS: {missing_text}\n"
                f"ORDER STATUS: {confirmed_text}"
            )

            ai_message = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(
                        content=f"CONVERSATION HISTORY:\n{history_text}\n\nCUSTOMER MESSAGE:\n{state['user_message']}"
                    ),
                ]
            )
            content = getattr(ai_message, "content", str(ai_message))
            if isinstance(content, list):
                content = "".join(
                    part.get("text", str(part)) if isinstance(part, dict) else str(part)
                    for part in content
                )
            return {"assistant_reply": str(content).strip()}
        except Exception as exc:  # noqa: BLE001
            err_msg = format_gemini_error(exc)
            return {"error": err_msg, "assistant_reply": err_msg}

    def route_after_retrieval(state: AssistantState) -> str:
        if state.get("error"):
            return "generate_response"
        intent = state.get("intent", "general_chat")
        has_removals = bool(state.get("remove_dish_names"))
        has_items = bool(state.get("validated_items")) or bool(state.get("unavailable_items"))

        if intent in ("order_request", "remove_item", "provide_details") or has_items or has_removals:
            return "collect_missing_details"
        if intent == "confirm_order":
            return "confirm_order"
        return "generate_response"

    def route_after_missing_details(state: AssistantState) -> str:
        if state.get("error"):
            return "generate_response"
        if state.get("validated_items") or state.get("remove_dish_names"):
            return "prepare_cart_update"
        if state.get("intent") == "confirm_order":
            return "confirm_order"
        return "generate_response"

    def route_after_cart_update(state: AssistantState) -> str:
        if state.get("error"):
            return "generate_response"
        if state.get("intent") == "confirm_order" and state.get("explicit_confirmation"):
            return "confirm_order"
        return "generate_response"

    graph = StateGraph(AssistantState)
    graph.add_node("understand_intent", understand_intent)
    graph.add_node("retrieve_menu_info", retrieve_menu_info)
    graph.add_node("collect_missing_details", collect_missing_details)
    graph.add_node("prepare_cart_update", prepare_cart_update)
    graph.add_node("confirm_order", confirm_order)
    graph.add_node("generate_response", generate_response)

    graph.add_edge(START, "understand_intent")
    graph.add_edge("understand_intent", "retrieve_menu_info")
    graph.add_conditional_edges(
        "retrieve_menu_info",
        route_after_retrieval,
        {
            "confirm_order": "confirm_order",
            "collect_missing_details": "collect_missing_details",
            "generate_response": "generate_response",
        },
    )
    graph.add_conditional_edges(
        "collect_missing_details",
        route_after_missing_details,
        {
            "prepare_cart_update": "prepare_cart_update",
            "confirm_order": "confirm_order",
            "generate_response": "generate_response",
        },
    )
    graph.add_conditional_edges(
        "prepare_cart_update",
        route_after_cart_update,
        {
            "confirm_order": "confirm_order",
            "generate_response": "generate_response",
        },
    )
    graph.add_edge("confirm_order", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()


def run_assistant_turn(
    user_message: str,
    chat_history: list[dict[str, str]],
    current_cart: list[dict[str, Any]],
    customer_details: dict[str, str],
    llm_factory: Callable[[float], Any] | None = None,
) -> AssistantState:
    """Execute one complete LangGraph turn for the AI Order Assistant."""
    compiled = build_ordering_graph(llm_factory=llm_factory)
    initial_state: AssistantState = {
        "user_message": user_message,
        "chat_history": list(chat_history),
        "current_cart": deepcopy(current_cart),
        "working_cart": deepcopy(current_cart),
        "customer_details": dict(customer_details),
        "intent": "general_chat",
        "explicit_confirmation": False,
        "search_keywords": [],
        "dietary_filter": "All",
        "extracted_items": [],
        "remove_dish_names": [],
        "validated_items": [],
        "unavailable_items": [],
        "retrieved_menu_context": "",
        "missing_details": [],
        "spice_clarifications": [],
        "cart_actions": [],
        "order_confirmed": False,
        "confirmed_order": None,
        "assistant_reply": "",
        "error": None,
    }
    return compiled.invoke(initial_state)
