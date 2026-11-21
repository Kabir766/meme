# DESI BITES — Modern Indian Restaurant AI Ordering App

**Desi Bites** is a Python-only, mobile-friendly Indian restaurant ordering application built with **Streamlit**, **LangChain**, **LangGraph**, and the **Google Gemini API** (`langchain-google-genai`).

Customers can browse curated Vegetarian and Non-Vegetarian Indian menus, customize spice levels and dish options, chat naturally with a Gemini-powered AI Order Assistant to ask about ingredients or build their order, manage their cart, and submit demo orders.

---

## Features

1. **Home** — Custom Desi Bites brand identity, dark charcoal & saffron palette, featured dishes, today's chef specials, and quick navigation.
2. **Menu** — Separate **Vegetarian** and **Non-Vegetarian** tabs across 7 categories (*Starters*, *Main Course*, *Breads*, *Rice and Biryani*, *Snacks*, *Desserts*, *Beverages*), live search, category filter, and per-dish customization popovers.
3. **AI Order Assistant** — Stateful **LangGraph** workflow (`understand_intent` → `retrieve_menu_info` → `collect_missing_details` → `prepare_cart_update` → `confirm_order` → `generate_response`) grounded strictly in `data/menu.py` so items and INR prices are never invented.
4. **Cart & Checkout** — Quantity controls, dish removal, live subtotal, automatic delivery fee calculation (`₹40` under `₹599`, **Free** at `₹599+` or for Pickup), and customer checkout details.
5. **Order Confirmation** — Generates a demo order ID (`DB-YYYYMMDD-XXXX`), full itemized receipt, and confirmation summary (no real payment or delivery APIs).

---

## Project Structure

```text
desi-bites/
├── .streamlit/
│   └── config.toml          # Dark charcoal, saffron accent, warm ivory Streamlit theme
├── assets/
│   └── images/              # Curated dark-studio food imagery
├── backend/
│   ├── __init__.py
│   ├── config.py            # Loads GEMINI_API_KEY & GEMINI_MODEL via python-dotenv
│   ├── gemini_client.py     # ChatGoogleGenerativeAI factory & friendly error mapping
│   ├── graph.py             # Typed LangGraph customer ordering workflow
│   └── order_service.py     # Cart operations, INR billing, validation, demo orders
├── data/
│   ├── __init__.py
│   └── menu.py              # Authoritative Indian restaurant menu catalog (INR)
├── tests/
│   └── test_app.py          # Automated tests for menu, cart, config, graph & Streamlit UI
├── .env.example             # Environment variable placeholders (safe to commit)
├── .gitignore               # Excludes .env, .venv, __pycache__, secrets
├── app.py                   # Main Streamlit application (all 5 sections)
├── metadata.json            # App metadata
├── README.md
└── requirements.txt         # Python dependencies
```

---

## Configuration (Where to Enter Your Gemini API Key)

No API key is included or hardcoded in this repository.

1. Copy `.env.example` to `.env` in the project root folder (`desi-bites/.env`):
   ```bash
   cp .env.example .env
   ```
   *(On Windows PowerShell: `Copy-Item .env.example .env`)*
2. Open `.env` and paste your own free Google AI Studio key on the `GEMINI_API_KEY=` line (`GEMINI_MODEL=gemini-2.5-flash` is already pre-filled for the free tier):
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. **Important:** Never commit `.env` to GitHub (`.gitignore` already excludes it).

If `GEMINI_API_KEY` is missing or left blank, the Menu and Cart still work normally, and the AI Order Assistant displays a helpful configuration prompt.

---

## Running Locally on Windows

1. **Install Python 3.10+** from [python.org](https://www.python.org/downloads/) (check **"Add python.exe to PATH"** during installation).
2. **Open Command Prompt or PowerShell** inside the project folder and create a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Create `.env`** from `.env.example` and enter your `GEMINI_API_KEY` and `GEMINI_MODEL`.
5. **Run the app**:
   ```powershell
   streamlit run app.py
   ```
6. Open the local URL shown in the terminal (typically `http://localhost:8501`).

---

## Running Tests

```bash
pytest -v
```

---

## Deployment Instructions

### Option 1: Streamlit Community Cloud (Recommended for Streamlit)

1. Push this repository to GitHub (`.gitignore` ensures `.env` and `.venv` are excluded).
2. Sign in to [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
3. Click **New app**, select your repository, branch, and set **Main file path** to `app.py`.
4. Open **Advanced settings → Secrets** and add:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```
5. Click **Deploy**.

### Option 2: Render (Web Service)

1. Push this repository to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com) connected to your repo.
3. Configure:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Under **Environment Variables**, add `GEMINI_API_KEY` and `GEMINI_MODEL`.
5. Deploy the service.

### Why Streamlit Cannot Be Deployed as a Conventional Netlify Static Site

Netlify's standard hosting serves **static frontend files** (HTML/CSS/JS bundles) and lightweight serverless functions. **Streamlit requires a persistent Python server process and active WebSocket connections** to manage widget callbacks and `st.session_state`, so a `streamlit run app.py` app cannot run directly on Netlify static hosting.

If deployment on Netlify were strictly required, you would need a **split architecture**:
- A **static frontend** (e.g., React/Next.js/HTML) hosted on Netlify, and
- A **separate Python API backend** (e.g., FastAPI running LangGraph + Gemini) hosted on a Python-capable platform such as Render, Railway, or Google Cloud Run.
