# AI Recovery Agent

An intelligent, full-stack automated debt collection system designed to help businesses recover overdue invoices with zero manual effort. The system leverages AI to draft context-aware, polite-but-firm emails, dynamically generates secure Razorpay payment links, and manages everything in a beautiful real-time React dashboard.

> ✅ **Deployment Status:** Live! You can access the dashboard here: **[https://recovery-agent-theta.vercel.app](https://recovery-agent-theta.vercel.app)**. 
> *(Note: The backend is hosted on Render. The SendGrid Inbound Parse email webhook is fully built and tested, but requires the purchase of a custom domain before it can route live replies in production).*

## 💡 What Does This Project Solve?
For most businesses, chasing down overdue payments is incredibly painful. Employees waste hours manually tracking which invoices are late, writing awkward follow-up emails, and manually generating payment links. Worse, sending aggressive emails too early can ruin client relationships, while waiting too long reduces the chance of getting paid. 

**The AI Recovery Agent solves this by fully automating the collection cycle:**
- **Zero Human Effort:** The background agent autonomously scans for overdue invoices every day and handles the outreach completely on its own.
- **Intelligent Escalation:** The AI dynamically adjusts its tone based on how late the invoice is (gentle reminder at 5 days, strict at 15 days, urgent at 25 days) to protect client relationships.
- **Frictionless Payments:** By embedding 1-click Razorpay links directly into the AI-generated emails, it removes all friction for the customer, resulting in faster payments and significantly improved cash flow.

## 🚀 Key Features
- **Automated Daily Batch Jobs**: A background scheduler runs every morning at 8:00 AM, scanning the database for overdue invoices.
- **Context-Aware AI Generation**: Integrates with Groq (`qwen3.8-27b`) to analyze how many days an invoice is overdue and dynamically generates a personalized, perfectly toned email paragraph.
- **Dynamic Payment Links**: Connects to the Razorpay API to generate secure, short URLs for customers to pay their exact balance. *(Note: Currently configured for INR to INR domestic transactions only)*.
- **SendGrid Integration**: Automatically dispatches the AI-drafted emails with the payment links seamlessly injected.
- **Employee Dashboard**: A gorgeous, glassmorphism React dashboard for employees to monitor recovery metrics, manually resend links, negotiate extensions, or write-off bad debt.

## 🏗️ Architecture Design:
[View Architecture Design](https://www.tldraw.com/f/kdBJw2HelYW1qoRQqS28F?d=v-3395.-2866.9701.5567.page)

**Invoice Ingestion:** Invoice data ingestion is currently handled via local database seeding (serving as a stand-in for CSV imports). A production deployment would sync directly from the merchant's invoicing or ERP system (e.g., Tally, Zoho Books, QuickBooks, custom DBs) via scheduled API polling. This incoming data is then normalized into the application's schema—the current synthetic data script is the exact seam where this enterprise integration plugs in. This deliberate boundary keeps the recovery agent strictly focused on its core responsibility: intelligent collection.

---

## 📁 Project Structure

```text
recovery-agent/
├── backend/               # FastAPI Python application
│   ├── app/               # Core application logic
│   │   ├── agent/         # AI integrations (Groq orchestration & tone logic)
│   │   ├── db/            # SQLModel database schemas and connection
│   │   ├── integrations/  # External API clients (SendGrid, Razorpay, Groq)
│   │   ├── routes/        # FastAPI endpoints (Auth, Invoices, Webhooks, Analytics)
│   │   ├── main.py        # Backend entry point
│   │   └── scheduler.py   # APScheduler for daily background jobs
│   ├── scripts/           # DB seeding and manual execution scripts
│   ├── tests/             # Unit and integration tests
│   └── requirements.txt   # Python dependencies
│
├── frontend/              # React + Vite application
│   ├── src/
│   │   ├── api/           # Axios API client for backend communication
│   │   ├── components/    # Reusable React components (InvoiceTable, MetricsCards)
│   │   ├── pages/         # High-level page components (Dashboard, Login)
│   │   ├── App.jsx        # App router and layout
│   │   └── main.jsx       # React entry point
│   ├── package.json       # Node.js dependencies
│   └── vite.config.js     # Vite bundler configuration
│
└── Readme.md              # Project documentation
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- A Neon PostgreSQL Database (or any PostgreSQL instance)
- API Keys for **Groq**, **SendGrid**, and **Razorpay**

### 2. Environment Variables
Create a `.env` file inside the `backend/` directory with the following variables:
```env
DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
JWT_SECRET="your_super_secret_jwt_key"
ENVIRONMENT="DEV"

GROQ_API_KEY="your_groq_api_key"
SENDGRID_API_KEY="your_sendgrid_api_key"
FROM_EMAIL="your_verified_sender_email@gmail.com"

RAZORPAY_KEY_ID="your_razorpay_key_id"
RAZORPAY_KEY_SECRET="your_razorpay_key_secret"
RAZORPAY_WEBHOOK_SECRET="your_razorpay_webhook_secret"
```

### 3. Backend Setup
Open a terminal and run the following commands:
```bash
cd backend
python -m venv venv
# Activate virtual environment (Windows)
venv\Scripts\activate
# Activate virtual environment (Mac/Linux)
# source venv/bin/activate

pip install -r requirements.txt
```

### 4. Frontend Setup
Open a *second* terminal and run:
```bash
cd frontend
npm install
```

---

## 🏃‍♂️ How to Run the Application

You will need to run the frontend and backend simultaneously in two separate terminals.

**1. Start the Backend Server**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```
*The backend API will be available at `http://localhost:8000`. You can view the interactive API documentation at `http://localhost:8000/docs`.*

**2. Start the Frontend Application**
```bash
cd frontend
npm run dev
```
*The React application will be available at `http://localhost:5173`.*

**3. Default Login Credentials**
If you seeded the database using the provided script, use the following credentials to access the Dashboard:
- **Username:** `admin`
- **Password:** `password123`

---

## 🔧 Useful Scripts
If you want to manually test the daily AI batch script without waiting for 8:00 AM, you can run:
```bash
cd backend
python scripts/run_batch.py
```

If you need to reset the database and seed it with dummy invoices:
```bash
cd backend
python scripts/seed_synthetic_data.py
```
