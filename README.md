# JaneMaiks Retail Assistant 🏪

**AI-powered retail management system** for **JaneMaiks** — a real Kenyan retail business. Supports **wholesale + retail pricing workflows**, inventory management, analytics, and a smart chatbot with Swahili support. Custom-built for JaneMaiks.

## Architecture

```
janemaiks-retail-assistant/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point + migration
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # SQLite + SQLAlchemy setup
│   │   ├── models/          # Database models (Product, Inventory, Chat)
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic (pricing, RAG, chat)
│   │   └── seed.py          # Sample data seeder
│   ├── .env                 # Environment variables
│   └── requirements.txt
├── frontend/                 # React + TailwindCSS frontend
│   ├── public/
│   │   ├── favicon.svg      # JaneMaiks branded favicon
│   │   ├── app-icon.svg     # JaneMaiks PWA app icon
│   │   ├── splash-icon.svg  # JaneMaiks splash screen
│   │   └── manifest.json    # JaneMaiks PWA manifest
│   ├── src/
│   │   ├── components/
│   │   │   ├── Logo.jsx     # JaneMaiks branded logo component
│   │   │   └── ...          # Branded UI components
│   │   ├── pages/           # Dashboard, Products, Chatbot, Analytics
│   │   ├── services/        # API client (axios)
│   │   ├── hooks/           # Custom hooks (theme)
│   │   ├── App.jsx          # Router + layout
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## JaneMaiks Brand Identity

| Element          | Value                          |
|------------------|--------------------------------|
| Business Name    | JaneMaiks                      |
| App Name         | JaneMaiks Retail Assistant     |
| Primary Color    | `#0047AB` (Deep Cobalt Blue)   |
| Secondary Color  | `#2E8B57` (Forest Green)       |
| Accent Color     | `#FF6F00` (Vibrant Orange)     |
| Background       | `#FFFFFF`                      |
| Text Color       | `#333333`                      |
| Logo Mark        | JM monogram in a rounded badge |
| Font             | Inter                          |

## Tech Stack

| Layer       | Technology                           |
|-------------|--------------------------------------|
| Backend     | Python FastAPI, SQLAlchemy, SQLite   |
| Frontend    | React 18, Vite, TailwindCSS          |
| AI/Search   | ChromaDB (vector store), fuzzy matching |
| Validation  | Pydantic                             |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The JaneMaiks API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The JaneMaiks app will open at `http://localhost:5173`

### 3. Quick Start (Windows)

Double-click `start.bat` to launch both services.

## API Endpoints

### Products
| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| GET    | /api/products/              | List products (searchable) |
| POST   | /api/products/              | Create product (auto-calc) |
| PUT    | /api/products/{id}          | Update product             |
| DELETE | /api/products/{id}          | Soft-delete product        |
| GET    | /api/products/categories/list | List distinct categories |
| GET    | /api/products/suppliers/list  | List distinct suppliers  |

### Pricing
| Method | Endpoint                       | Description                          |
|--------|--------------------------------|--------------------------------------|
| POST   | /api/pricing/calculate         | Calculate retail price (legacy)      |
| GET    | /api/pricing/batch             | Batch price lookup                   |
| POST   | /api/pricing/suggest           | Suggest retail price with rounding   |
| GET    | /api/pricing/product/{id}      | Get full pricing for a product       |
| POST   | /api/pricing/round             | Round a price (nearest_5/nearest_10) |
| POST   | /api/pricing/calculate-full    | Real-time calc from raw inputs       |

### Chat
| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| POST   | /api/chat/query             | Chat with JaneMaiks AI     |
| GET    | /api/chat/history           | Chat history               |

### Inventory & Analytics
| Method | Endpoint                    | Description                |
|--------|-----------------------------|----------------------------|
| GET    | /api/inventory/             | List inventory             |
| POST   | /api/inventory/transactions | Add/deduct stock           |
| GET    | /api/analytics/dashboard    | JaneMaiks dashboard stats  |
| GET    | /api/health                 | Health check               |

## Features

### JaneMaiks Wholesale + Retail Pricing Engine
- **Package Cost:** JaneMaiks buys products in bulk (e.g., 1 dozen at KSh 390)
- **Unit Cost:** Automatically calculated (390 / 12 = 32.5)
- **Profit Margin:** Set per-unit profit in KSh
- **Suggested Retail:** Auto-calculated (unit cost + profit)
- **Rounding:** Nearest 5 (42.5 → 45) or Nearest 10 (42.5 → 40)
- **Manual Override:** Shop owner can set a fixed retail price
- **Wholesale Selling:** Price to sell whole package to other shopkeepers
- **Profit Analysis:** Per-unit and per-package profit display

### Pricing Hierarchy
1. If `allow_manual_override` is ON and `actual_retail_price` is set → use it
2. Otherwise → `unit_cost_price + profit_margin_per_unit` → apply rounding

### JaneMaiks AI Assistant (Chatbot)
- **Retail price queries** ("How much is Arimis?")
- **Wholesale price queries** ("What is the wholesale price of Arimis?")
- **Unit cost queries** ("How much do we buy a dozen at?")
- **Profit queries** ("How much profit per unit?")
- **Package details** ("Package info for milk")
- **Price suggestions** ("Suggest selling price for this item")
- Fuzzy matching + semantic search
- Swahili support ("Bei gani ya sukari?")
- Stock queries ("How many sweets remaining?")
- Supplier queries ("Products from Bidco")

### Business Intelligence
- Profit per unit and per package display
- Low-margin warnings (< KSh 5/unit)
- Manual vs suggested price comparison
- Wholesale pricing summary
- Accurate daily/monthly profit estimates
- Low stock alerts

### RAG (Retrieval-Augmented Generation)
Uses ChromaDB vector store to semantically search product descriptions.
Falls back to fuzzy string matching if ChromaDB is unavailable.

### Example Chat Prompts
```
- "How much is Arimis Petroleum Jelly?"
- "What is the wholesale price of Arimis?"
- "How much profit per unit on Arimis?"
- "How much do we buy a dozen at?"
- "Suggest selling price for this item"
- "What is the unit cost of cooking oil?"
- "How many sweets are remaining?"
- "Bei gani ya sukari?"
- "Zimesalia ngapi?"
- "Calculate price for 5 units"
```

## Product Model (New Fields)

| Field                    | Type    | Description                          |
|--------------------------|---------|--------------------------------------|
| package_cost_price       | Float   | Price paid for the whole package     |
| package_quantity         | Integer | Units per package                    |
| package_unit_type        | String  | Unit type (piece, packet, bottle...) |
| unit_cost_price          | Float   | Auto-calculated (cost / quantity)    |
| wholesale_selling_price  | Float   | Price to sell whole package (B2B)    |
| suggested_retail_price   | Float   | Auto-calculated (cost + margin)      |
| actual_retail_price      | Float   | Manually overridden retail price     |
| profit_margin_per_unit   | Float   | Profit per unit in KSh               |
| allow_manual_override    | Boolean | Enables manual retail price override |
| rounding_strategy        | String  | none / nearest_5 / nearest_10        |

## Environment Variables

| Variable              | Default                        | Description          |
|-----------------------|--------------------------------|----------------------|
| DATABASE_URL          | sqlite:///./retail_assistant.db | SQLite database path |
| DEFAULT_PROFIT_MARGIN | 15                            | Default margin %     |
| EMBEDDING_MODEL       | all-MiniLM-L6-v2              | Sentence transformer |
| CHROMA_PERSIST_DIR    | ./chroma_db                   | Vector store path    |
| CORS_ORIGINS          | http://localhost:5173          | Allowed origins      |

## Mobile Deployment

JaneMaiks Retail Assistant is PWA-ready:
- `public/manifest.json` — PWA manifest with JaneMaiks branding
- `public/app-icon.svg` — JaneMaiks app icon (512x512, maskable)
- `public/splash-icon.svg` — JaneMaiks splash screen (1280x720)
- Meta tags in `index.html` for iOS/Android home screen support

## License

MIT
