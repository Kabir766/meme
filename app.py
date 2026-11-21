"""Desi Bites — Modern Indian Restaurant AI Ordering App (Streamlit)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from backend.config import get_gemini_model_name, is_gemini_configured
from backend.graph import run_assistant_turn
from backend.order_service import (
    FREE_DELIVERY_THRESHOLD_INR,
    ORDER_TYPES,
    add_to_cart,
    calculate_order_totals,
    clear_cart,
    create_demo_order,
    remove_from_cart,
    update_cart_quantity,
)
from data.menu import (
    CATEGORIES,
    SPICE_LEVELS,
    MenuItem,
    get_featured_items,
    get_todays_specials,
    search_menu,
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "images"

NAV_SECTIONS = [
    "Home",
    "Menu",
    "AI Order Assistant",
    "Cart & Checkout",
    "Order Confirmation",
]


def _inject_custom_css() -> None:
    """Apply dark charcoal, saffron accent, warm ivory, and rounded card styling."""
    st.markdown(
        """
        <style>
        /* Layout & App Container */
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }

        /* Brand Header */
        .db-brand-wrap {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.75rem;
            padding: 0.85rem 1.15rem;
            border-radius: 16px;
            background: linear-gradient(135deg, #1A1A20 0%, #141418 100%);
            border: 1px solid rgba(249, 115, 22, 0.28);
            margin-bottom: 1rem;
        }
        .db-logo {
            font-size: 1.65rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            line-height: 1.1;
            color: #FAF5EE;
            margin: 0;
        }
        .db-logo span {
            color: #F97316;
        }
        .db-tagline {
            font-size: 0.74rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #B8B0A4;
            margin-top: 0.2rem;
        }
        .db-pill {
            display: inline-block;
            padding: 0.28rem 0.72rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            background: rgba(249, 115, 22, 0.14);
            color: #FB923C;
            border: 1px solid rgba(249, 115, 22, 0.35);
        }

        /* Cards */
        .db-card {
            background: #1C1C21;
            border: 1px solid rgba(250, 245, 238, 0.09);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.85rem;
        }
        .db-hero-card {
            background: linear-gradient(135deg, #211B16 0%, #17171C 70%);
            border: 1px solid rgba(249, 115, 22, 0.25);
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            margin-bottom: 1rem;
        }
        .db-dish-title {
            font-size: 1.06rem;
            font-weight: 700;
            color: #FAF5EE;
            margin: 0.15rem 0 0.25rem 0;
        }
        .db-price {
            font-size: 1.05rem;
            font-weight: 700;
            color: #F97316;
        }
        .db-muted {
            color: #B8B0A4;
            font-size: 0.88rem;
            line-height: 1.45;
        }

        /* Dietary Badges */
        .db-badge-veg {
            display: inline-block;
            font-size: 0.73rem;
            font-weight: 700;
            color: #4ADE80;
            background: rgba(74, 222, 128, 0.12);
            border: 1px solid rgba(74, 222, 128, 0.32);
            padding: 0.12rem 0.5rem;
            border-radius: 999px;
        }
        .db-badge-nonveg {
            display: inline-block;
            font-size: 0.73rem;
            font-weight: 700;
            color: #F87171;
            background: rgba(248, 113, 113, 0.12);
            border: 1px solid rgba(248, 113, 113, 0.35);
            padding: 0.12rem 0.5rem;
            border-radius: 999px;
        }
        .db-badge-meta {
            display: inline-block;
            font-size: 0.73rem;
            font-weight: 600;
            color: #E7DEC8;
            background: rgba(250, 245, 238, 0.07);
            padding: 0.12rem 0.5rem;
            border-radius: 999px;
            margin-left: 0.3rem;
        }

        /* Rounded images & Buttons */
        [data-testid="stImage"] img {
            border-radius: 14px;
            border: 1px solid rgba(250, 245, 238, 0.08);
        }
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.15s ease;
        }
        .stButton > button[kind="primary"] {
            background-color: #F97316;
            color: #121215;
            border: none;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #FB923C;
            color: #121215;
        }

        /* Confirmation Box */
        .db-confirm-box {
            background: linear-gradient(135deg, rgba(74, 222, 128, 0.10), rgba(249, 115, 22, 0.10));
            border: 1px solid rgba(74, 222, 128, 0.38);
            border-radius: 18px;
            padding: 1.35rem;
            margin-bottom: 1rem;
        }

        /* Mobile tweaks */
        @media (max-width: 640px) {
            .db-logo { font-size: 1.35rem; }
            .block-container { padding-left: 0.85rem; padding-right: 0.85rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state() -> None:
    """Initialize required Streamlit session state keys cleanly."""
    defaults: dict[str, object] = {
        "active_section": "Home",
        "cart": [],
        "chat_history": [
            {
                "role": "assistant",
                "content": (
                    "Namaste! Welcome to **Desi Bites**. I can help you explore our menu, check "
                    "ingredients or spice levels, recommend dishes, and build your order. "
                    "What are you craving today?"
                ),
            }
        ],
        "customer_details": {
            "name": "",
            "phone": "",
            "address": "",
            "order_type": "Delivery",
            "notes": "",
        },
        "demo_orders": [],
        "latest_order": None,
        "flash_notice": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _navigate(section: str) -> None:
    st.session_state["active_section"] = section
    st.rerun()


def _quick_add_item(
    item: MenuItem,
    quantity: int = 1,
    spice_level: str | None = None,
    customizations: list[str] | None = None,
    special_instructions: str = "",
) -> None:
    updated, _, err = add_to_cart(
        st.session_state["cart"],
        item_identifier=item.id,
        quantity=quantity,
        spice_level=spice_level,
        customizations=customizations,
        special_instructions=special_instructions,
    )
    if err:
        st.session_state["flash_notice"] = ("error", err)
    else:
        st.session_state["cart"] = updated
        st.session_state["flash_notice"] = (
            "success",
            f"Added {quantity}x {item.name} (₹{item.price_inr * quantity}) to your cart.",
        )


def _dietary_badge_html(dietary: str) -> str:
    if dietary == "Veg":
        return '<span class="db-badge-veg">● VEG</span>'
    return '<span class="db-badge-nonveg">▲ NON-VEG</span>'


def _render_header_and_nav() -> None:
    order_type = st.session_state["customer_details"].get("order_type", "Delivery")
    totals = calculate_order_totals(st.session_state["cart"], order_type=order_type)
    cart_count = totals["item_count"]

    st.markdown(
        f"""
        <div class="db-brand-wrap">
            <div>
                <div class="db-logo">DESI <span>BITES</span></div>
                <div class="db-tagline">Modern Indian Kitchen • Tandoor • Biryani • Chai</div>
            </div>
            <div>
                <span class="db-pill">Cart: {cart_count} item{"s" if cart_count != 1 else ""} • ₹{totals["total_inr"]}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compact responsive top navigation bar
    nav_cols = st.columns(len(NAV_SECTIONS))
    active = st.session_state["active_section"]
    for idx, section in enumerate(NAV_SECTIONS):
        label = section
        if section == "Cart & Checkout" and cart_count > 0:
            label = f"Cart ({cart_count})"
        btn_type = "primary" if active == section else "secondary"
        with nav_cols[idx]:
            if st.button(label, key=f"nav_{section}", use_container_width=True, type=btn_type):
                _navigate(section)

    # Flash confirmation banner after actions
    notice = st.session_state.pop("flash_notice", None)
    if notice:
        kind, msg = notice
        if kind == "success":
            st.success(msg)
        else:
            st.error(msg)


def _render_sidebar() -> None:
    order_type = st.session_state["customer_details"].get("order_type", "Delivery")
    totals = calculate_order_totals(st.session_state["cart"], order_type=order_type)

    with st.sidebar:
        st.markdown("### DESI BITES")
        st.caption("Modern Indian Dining & AI Ordering")
        st.divider()

        st.markdown("**Quick Navigation**")
        for section in NAV_SECTIONS:
            prefix = "▸ " if st.session_state["active_section"] == section else ""
            if st.button(f"{prefix}{section}", key=f"side_nav_{section}", use_container_width=True):
                _navigate(section)

        st.divider()
        st.markdown("**Live Cart**")
        if not st.session_state["cart"]:
            st.caption("Your cart is empty. Browse the menu or ask our AI assistant to build an order.")
        else:
            for item in st.session_state["cart"]:
                line_total = item["unit_price_inr"] * item["quantity"]
                st.markdown(f"- **{item['quantity']}x {item['name']}** — ₹{line_total}")
            st.markdown(f"**Subtotal:** ₹{totals['subtotal_inr']}")
            fee_label = "FREE" if totals["delivery_fee_inr"] == 0 else f"₹{totals['delivery_fee_inr']}"
            st.markdown(f"**Delivery Fee:** {fee_label}")
            st.markdown(f"**Total:** ₹{totals['total_inr']}")
            if st.button("Proceed to Checkout", type="primary", use_container_width=True, key="side_checkout"):
                _navigate("Cart & Checkout")

        st.divider()
        st.caption(f"Free delivery on orders ₹{FREE_DELIVERY_THRESHOLD_INR}+ • Demo Mode")


def _render_dish_card(item: MenuItem, key_prefix: str, show_image: bool = False) -> None:
    with st.container(border=True):
        if show_image and item.image_path:
            img_file = Path(__file__).resolve().parent / item.image_path
            if img_file.exists() and img_file.stat().st_size > 0:
                st.image(str(img_file), width="stretch")

        badges = (
            f"{_dietary_badge_html(item.dietary)}"
            f'<span class="db-badge-meta">{item.category}</span>'
            f'<span class="db-badge-meta">{item.spice_level}</span>'
            f'<span class="db-badge-meta">~{item.prep_time_mins}m</span>'
        )
        st.markdown(badges, unsafe_allow_html=True)

        title_col, price_col = st.columns([3, 1])
        with title_col:
            st.markdown(f'<div class="db-dish-title">{item.name}</div>', unsafe_allow_html=True)
        with price_col:
            st.markdown(
                f'<div class="db-price" style="text-align:right;">₹{item.price_inr}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(f'<div class="db-muted">{item.description}</div>', unsafe_allow_html=True)
        st.caption(f"Key ingredients: {', '.join(item.ingredients[:5])}")

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            if st.button("+ Quick Add", key=f"{key_prefix}_quick_{item.id}", use_container_width=True):
                _quick_add_item(item, quantity=1)
                st.rerun()

        with btn_col2:
            with st.popover("Customize", use_container_width=True):
                qty = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=20,
                    value=1,
                    step=1,
                    key=f"{key_prefix}_qty_{item.id}",
                )
                chosen_spice = item.spice_level
                if item.customizable_spice:
                    default_idx = SPICE_LEVELS.index(item.spice_level) if item.spice_level in SPICE_LEVELS else 1
                    chosen_spice = st.selectbox(
                        "Spice Level",
                        options=SPICE_LEVELS,
                        index=default_idx,
                        key=f"{key_prefix}_spice_{item.id}",
                    )
                chosen_customs = []
                if item.customizations:
                    chosen_customs = st.multiselect(
                        "Customizations",
                        options=item.customizations,
                        key=f"{key_prefix}_cust_{item.id}",
                    )
                notes = st.text_input(
                    "Special Instructions (optional)",
                    placeholder="e.g., Less oil, pack chutney separately",
                    key=f"{key_prefix}_notes_{item.id}",
                )
                if st.button(
                    f"Add to Cart • ₹{item.price_inr * int(qty)}",
                    type="primary",
                    use_container_width=True,
                    key=f"{key_prefix}_add_{item.id}",
                ):
                    _quick_add_item(
                        item,
                        quantity=int(qty),
                        spice_level=chosen_spice,
                        customizations=chosen_customs,
                        special_instructions=notes,
                    )
                    st.rerun()


def _render_home() -> None:
    hero_col1, hero_col2 = st.columns([1.25, 1], gap="large")
    with hero_col1:
        st.markdown(
            """
            <div class="db-hero-card">
                <div class="db-pill" style="margin-bottom:0.7rem;">Chef's Kitchen Open • Demo Ordering</div>
                <h1 style="margin:0 0 0.5rem 0; color:#FAF5EE; font-size:2rem; line-height:1.15;">
                    Bold Indian Classics, <span style="color:#F97316;">Crafted Fresh.</span>
                </h1>
                <p class="db-muted" style="font-size:0.97rem; margin-bottom:0.85rem;">
                    Slow-simmered 24-hour dals, smoky clay-oven kebabs, saffron-kissed dum biryanis,
                    and kulhad chai — browse our curated Vegetarian &amp; Non-Vegetarian menus or let
                    our Gemini-powered AI Order Assistant tailor your meal.
                </p>
                <div class="db-muted" style="font-size:0.84rem;">
                    ✓ Free delivery above ₹599 &nbsp;•&nbsp; ✓ Custom spice levels &nbsp;•&nbsp; ✓ Instant AI order builder
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cta1, cta2, cta3 = st.columns(3)
        with cta1:
            if st.button("Explore Menu", type="primary", use_container_width=True, key="home_menu_btn"):
                _navigate("Menu")
        with cta2:
            if st.button("AI Order Assistant", use_container_width=True, key="home_ai_btn"):
                _navigate("AI Order Assistant")
        with cta3:
            if st.button("Go to Cart", use_container_width=True, key="home_cart_btn"):
                _navigate("Cart & Checkout")

    with hero_col2:
        hero_img = ASSETS_DIR / "desi_bites_hero.jpg"
        if hero_img.exists() and hero_img.stat().st_size > 0:
            st.image(str(hero_img), caption="Desi Bites Signature Feast", width="stretch")

    st.markdown("### Featured Dishes")
    featured = get_featured_items()[:6]
    cols = st.columns(2, gap="medium")
    for idx, item in enumerate(featured):
        with cols[idx % 2]:
            _render_dish_card(item, key_prefix="home_feat", show_image=item.image_path is not None and idx < 4)

    st.markdown("### Today's Specials")
    specials = get_todays_specials()
    sp_cols = st.columns(2, gap="medium")
    for idx, item in enumerate(specials):
        with sp_cols[idx % 2]:
            _render_dish_card(item, key_prefix="home_spec", show_image=False)


def _render_menu() -> None:
    st.markdown("## Desi Bites Menu")
    st.caption("Explore freshly prepared Vegetarian & Non-Vegetarian dishes. All prices in INR (₹).")

    filter_col1, filter_col2 = st.columns([2, 1])
    with filter_col1:
        search_query = st.text_input(
            "Search dishes or ingredients",
            placeholder="Try: paneer, biryani, garlic naan, saffron, mild...",
            key="menu_search_input",
        )
    with filter_col2:
        selected_category = st.selectbox(
            "Filter by Category",
            options=["All", *CATEGORIES],
            key="menu_category_filter",
        )

    veg_tab, nonveg_tab = st.tabs(["🌿 Vegetarian", "🔥 Non-Vegetarian"])

    with veg_tab:
        veg_items = search_menu(query=search_query, dietary="Veg", category=selected_category)
        if not veg_items:
            st.info("No vegetarian dishes match your current search/category filter.")
        else:
            _render_grouped_menu_grid(veg_items, key_prefix="menu_veg")

    with nonveg_tab:
        nonveg_items = search_menu(query=search_query, dietary="Non-Veg", category=selected_category)
        if not nonveg_items:
            if selected_category in ("Breads", "Desserts", "Beverages"):
                st.info(
                    f"All {selected_category} on our menu are 100% Vegetarian — "
                    "switch to the Vegetarian tab to explore them!"
                )
            else:
                st.info("No non-vegetarian dishes match your current search/category filter.")
        else:
            _render_grouped_menu_grid(nonveg_items, key_prefix="menu_nonveg")


def _render_grouped_menu_grid(items: list[MenuItem], key_prefix: str) -> None:
    for category in CATEGORIES:
        cat_items = [item for item in items if item.category == category]
        if not cat_items:
            continue
        st.markdown(f"#### {category}")
        cols = st.columns(2, gap="medium")
        for idx, item in enumerate(cat_items):
            with cols[idx % 2]:
                _render_dish_card(item, key_prefix=key_prefix, show_image=False)


def _render_ai_assistant() -> None:
    st.markdown("## AI Order Assistant")
    st.caption(
        f"Powered by LangGraph + LangChain + Gemini (`{get_gemini_model_name()}`). "
        "Ask about ingredients, spice levels, recommendations, or order conversationally."
    )

    configured, config_msg = is_gemini_configured()
    if not configured:
        st.error(config_msg or "GEMINI_API_KEY is missing.")
        st.info(
            "To enable the AI Order Assistant:\n"
            "1. Copy `.env.example` to `.env` in the project root.\n"
            "2. Set `GEMINI_API_KEY=your_actual_key` and `GEMINI_MODEL=gemini-2.5-flash`.\n"
            "3. Restart the Streamlit app."
        )
        return

    chat_col, summary_col = st.columns([1.85, 1], gap="large")

    with summary_col:
        with st.container(border=True):
            st.markdown("#### Live Cart Preview")
            order_type = st.session_state["customer_details"].get("order_type", "Delivery")
            totals = calculate_order_totals(st.session_state["cart"], order_type=order_type)
            if not st.session_state["cart"]:
                st.caption("No items yet. Try asking the assistant to add dishes!")
            else:
                for item in st.session_state["cart"]:
                    st.markdown(
                        f"**{item['quantity']}x {item['name']}** — ₹{item['unit_price_inr'] * item['quantity']}  \n"
                        f"<span class='db-muted'>Spice: {item['spice_level']}"
                        + (f" • {', '.join(item['customizations'])}" if item.get("customizations") else "")
                        + "</span>",
                        unsafe_allow_html=True,
                    )
                st.divider()
                st.markdown(f"**Subtotal:** ₹{totals['subtotal_inr']}")
                fee = "FREE" if totals["delivery_fee_inr"] == 0 else f"₹{totals['delivery_fee_inr']}"
                st.markdown(f"**Delivery ({order_type}):** {fee}")
                st.markdown(f"**Total:** ₹{totals['total_inr']}")
                if st.button("Review in Cart & Checkout", type="primary", use_container_width=True, key="ai_go_cart"):
                    _navigate("Cart & Checkout")

        with st.container(border=True):
            st.markdown("**Quick Prompts**")
            prompts = [
                "Recommend mild vegetarian mains and breads",
                "What are the ingredients in Paneer Tikka Masala?",
                "Add 1 Old Delhi Butter Chicken and 2 Garlic Butter Naan",
                "Show my current cart summary",
            ]
            for idx, prompt_text in enumerate(prompts):
                if st.button(prompt_text, key=f"quick_prompt_{idx}", use_container_width=True):
                    _process_ai_message(prompt_text)
                    st.rerun()

            if st.button("Reset Chat", key="reset_ai_chat", use_container_width=True):
                st.session_state["chat_history"] = [
                    {
                        "role": "assistant",
                        "content": "Fresh conversation started! What would you like to explore or order from Desi Bites?",
                    }
                ]
                st.rerun()

    with chat_col:
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.get("latest_order") and st.session_state["cart"] == []:
            if st.button("View Latest Order Confirmation →", type="primary", key="ai_view_confirm"):
                _navigate("Order Confirmation")

        user_input = st.chat_input("Ask about dishes or place an order (e.g., 'Add 1 Hyderabadi Chicken Biryani medium spice')...")
        if user_input:
            _process_ai_message(user_input)
            st.rerun()


def _process_ai_message(user_text: str) -> None:
    st.session_state["chat_history"].append({"role": "user", "content": user_text})
    with st.spinner("Checking Desi Bites kitchen & menu..."):
        result = run_assistant_turn(
            user_message=user_text,
            chat_history=st.session_state["chat_history"][:-1],
            current_cart=st.session_state["cart"],
            customer_details=st.session_state["customer_details"],
        )

    if not result.get("error"):
        st.session_state["cart"] = result["working_cart"]
        st.session_state["customer_details"] = result["customer_details"]

    if result.get("order_confirmed") and result.get("confirmed_order"):
        order_record = result["confirmed_order"]
        st.session_state["latest_order"] = order_record
        st.session_state["demo_orders"].insert(0, order_record)
        st.session_state["cart"] = clear_cart()

    reply = result.get("assistant_reply") or "Sorry, I could not generate a response right now."
    st.session_state["chat_history"].append({"role": "assistant", "content": reply})


def _render_cart_and_checkout() -> None:
    st.markdown("## Cart & Checkout")
    st.caption("Review quantities, customizations, and delivery details before submitting your demo order.")

    cart = st.session_state["cart"]
    if not cart:
        with st.container(border=True):
            st.info("Your cart is currently empty.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Browse Menu", type="primary", use_container_width=True, key="empty_cart_menu"):
                    _navigate("Menu")
            with c2:
                if st.button("Order with AI Assistant", use_container_width=True, key="empty_cart_ai"):
                    _navigate("AI Order Assistant")
        return

    items_col, checkout_col = st.columns([1.35, 1], gap="large")

    with items_col:
        st.markdown("#### Selected Dishes")
        for item in list(cart):
            cid = item["cart_item_id"]
            with st.container(border=True):
                top_l, top_r = st.columns([3, 1])
                with top_l:
                    st.markdown(_dietary_badge_html(item["dietary"]), unsafe_allow_html=True)
                    st.markdown(f"**{item['name']}**")
                    details_parts = [f"Spice: {item['spice_level']}"]
                    if item.get("customizations"):
                        details_parts.append("Custom: " + ", ".join(item["customizations"]))
                    if item.get("special_instructions"):
                        details_parts.append("Note: " + item["special_instructions"])
                    st.caption(" | ".join(details_parts))
                with top_r:
                    line_total = item["unit_price_inr"] * item["quantity"]
                    st.markdown(
                        f"<div class='db-price' style='text-align:right;'>₹{line_total}</div>"
                        f"<div class='db-muted' style='text-align:right; font-size:0.78rem;'>₹{item['unit_price_inr']} each</div>",
                        unsafe_allow_html=True,
                    )

                qty_c1, qty_c2, qty_c3, rm_c = st.columns([0.6, 0.7, 0.6, 1.5])
                with qty_c1:
                    if st.button("−", key=f"dec_{cid}", use_container_width=True):
                        st.session_state["cart"] = update_cart_quantity(cart, cid, item["quantity"] - 1)
                        st.rerun()
                with qty_c2:
                    st.markdown(
                        f"<div style='text-align:center; padding-top:0.4rem; font-weight:700;'>{item['quantity']}</div>",
                        unsafe_allow_html=True,
                    )
                with qty_c3:
                    if st.button("+", key=f"inc_{cid}", use_container_width=True):
                        st.session_state["cart"] = update_cart_quantity(cart, cid, item["quantity"] + 1)
                        st.rerun()
                with rm_c:
                    if st.button("Remove", key=f"rem_{cid}", use_container_width=True):
                        st.session_state["cart"] = remove_from_cart(cart, cid)
                        st.rerun()

        if st.button("Clear Entire Cart", key="clear_cart_btn"):
            st.session_state["cart"] = clear_cart()
            st.rerun()

    with checkout_col:
        with st.container(border=True):
            st.markdown("#### Order & Customer Details")
            details = st.session_state["customer_details"]

            order_type = st.radio(
                "Order Type",
                options=list(ORDER_TYPES),
                index=0 if details.get("order_type", "Delivery") == "Delivery" else 1,
                horizontal=True,
                key="checkout_order_type",
            )
            details["order_type"] = order_type

            totals = calculate_order_totals(st.session_state["cart"], order_type=order_type)

            if order_type == "Delivery" and totals["free_delivery_remaining_inr"] > 0:
                st.caption(
                    f"Add ₹{totals['free_delivery_remaining_inr']} more to unlock FREE delivery "
                    f"(orders ₹{FREE_DELIVERY_THRESHOLD_INR}+)."
                )
            elif order_type == "Delivery":
                st.caption("Free delivery unlocked on this order!")

            name = st.text_input("Full Name *", value=details.get("name", ""), placeholder="e.g., Aarav Sharma")
            phone = st.text_input("10-digit Phone Number *", value=details.get("phone", ""), placeholder="e.g., 9876543210")
            address = ""
            if order_type == "Delivery":
                address = st.text_area(
                    "Delivery Address *",
                    value=details.get("address", ""),
                    placeholder="Flat / House No., Street, Landmark, City",
                    height=80,
                )
            notes = st.text_input(
                "Kitchen / Delivery Instructions (optional)",
                value=details.get("notes", ""),
                placeholder="e.g., Ring bell twice, include extra napkins",
            )

            details["name"] = name
            details["phone"] = phone
            if order_type == "Delivery":
                details["address"] = address
            details["notes"] = notes
            st.session_state["customer_details"] = details

            st.divider()
            st.markdown("#### Bill Summary")
            b1, b2 = st.columns(2)
            b1.write("Items Subtotal")
            b2.markdown(f"<div style='text-align:right;'>₹{totals['subtotal_inr']}</div>", unsafe_allow_html=True)

            b3, b4 = st.columns(2)
            b3.write(f"Delivery Fee ({order_type})")
            fee_str = "FREE (₹0)" if totals["delivery_fee_inr"] == 0 else f"₹{totals['delivery_fee_inr']}"
            b4.markdown(f"<div style='text-align:right;'>{fee_str}</div>", unsafe_allow_html=True)

            b5, b6 = st.columns(2)
            b5.markdown("**Grand Total**")
            b6.markdown(
                f"<div class='db-price' style='text-align:right;'>₹{totals['total_inr']}</div>",
                unsafe_allow_html=True,
            )

            st.caption("Demo Checkout: No real payment or external delivery service will be charged.")

            if st.button(
                f"Confirm Demo Order • ₹{totals['total_inr']}",
                type="primary",
                use_container_width=True,
                key="submit_demo_order_btn",
            ):
                order_record, err = create_demo_order(st.session_state["cart"], details)
                if err or order_record is None:
                    st.error(err or "Please check your details and try again.")
                else:
                    st.session_state["latest_order"] = order_record
                    st.session_state["demo_orders"].insert(0, order_record)
                    st.session_state["cart"] = clear_cart()
                    _navigate("Order Confirmation")


def _render_order_confirmation() -> None:
    st.markdown("## Order Confirmation")
    latest = st.session_state.get("latest_order")

    if not latest:
        with st.container(border=True):
            st.info("You haven't placed a demo order in this session yet.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Browse Menu", type="primary", use_container_width=True, key="conf_menu"):
                    _navigate("Menu")
            with c2:
                if st.button("Chat with AI Assistant", use_container_width=True, key="conf_ai"):
                    _navigate("AI Order Assistant")
        return

    st.markdown(
        f"""
        <div class="db-confirm-box">
            <div class="db-badge-veg" style="margin-bottom:0.55rem;">✓ {latest['status']}</div>
            <h2 style="margin:0 0 0.25rem 0; color:#FAF5EE;">Thank you, {latest['customer']['name']}!</h2>
            <p class="db-muted" style="margin:0;">
                Your Desi Bites demo order has been recorded.<br/>
                <strong>Order ID:</strong> <span style="color:#F97316; font-weight:700;">{latest['order_id']}</span>
                &nbsp;•&nbsp; <strong>Placed:</strong> {latest['created_at']}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_left, c_right = st.columns([1.3, 1], gap="large")
    with c_left:
        with st.container(border=True):
            st.markdown("#### Order Summary")
            for item in latest["items"]:
                line_total = item["unit_price_inr"] * item["quantity"]
                st.markdown(f"**{item['quantity']}x {item['name']}** — ₹{line_total}")
                meta = [f"Spice: {item['spice_level']}"]
                if item.get("customizations"):
                    meta.append("Custom: " + ", ".join(item["customizations"]))
                if item.get("special_instructions"):
                    meta.append("Note: " + item["special_instructions"])
                st.caption(" | ".join(meta))

            st.divider()
            totals = latest["totals"]
            st.markdown(f"**Subtotal:** ₹{totals['subtotal_inr']}")
            st.markdown(f"**Delivery Fee:** ₹{totals['delivery_fee_inr']}")
            st.markdown(f"**Total (Demo):** ₹{totals['total_inr']}")

    with c_right:
        with st.container(border=True):
            st.markdown("#### Customer & Fulfillment")
            cust = latest["customer"]
            st.markdown(f"**Order Type:** {latest['order_type']}")
            st.markdown(f"**Name:** {cust['name']}")
            st.markdown(f"**Phone:** {cust['phone']}")
            st.markdown(f"**Address:** {cust['address']}")
            if cust.get("notes"):
                st.markdown(f"**Notes:** {cust['notes']}")
            st.markdown(f"**Payment:** {latest['payment_method']}")
            st.warning(latest["disclaimer"])

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Order Another Meal", type="primary", use_container_width=True, key="conf_new_order"):
            _navigate("Menu")
    with b2:
        if st.button("Back to Home", use_container_width=True, key="conf_home"):
            _navigate("Home")

    if len(st.session_state["demo_orders"]) > 1:
        with st.expander(f"Previous Demo Orders ({len(st.session_state['demo_orders']) - 1})"):
            for old in st.session_state["demo_orders"][1:]:
                st.markdown(
                    f"- **{old['order_id']}** ({old['created_at']}) — ₹{old['totals']['total_inr']} "
                    f"[{old['order_type']}]"
                )


def main() -> None:
    st.set_page_config(
        page_title="Desi Bites — Modern Indian Kitchen",
        page_icon="🍛",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_custom_css()
    _init_session_state()
    _render_sidebar()
    _render_header_and_nav()

    section = st.session_state["active_section"]
    if section == "Home":
        _render_home()
    elif section == "Menu":
        _render_menu()
    elif section == "AI Order Assistant":
        _render_ai_assistant()
    elif section == "Cart & Checkout":
        _render_cart_and_checkout()
    elif section == "Order Confirmation":
        _render_order_confirmation()
    else:
        _render_home()


if __name__ == "__main__":
    main()
