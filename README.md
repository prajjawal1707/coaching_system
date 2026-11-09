# FeeFlow – Coaching Institute Fee Management System

**FeeFlow** is a fee-management prototype designed for a coaching institute operating multiple centres. It brings student fee records, instalments, parent access, payment tracking, reminders, refunds, academic records and accounts reporting into one application.

**Repository:** https://github.com/prajjawal1707/coaching_system

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Authentication and Demo Access](#authentication-and-demo-access)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Important API Workflows](#important-api-workflows)
- [Prototype Notes and Production Considerations](#prototype-notes-and-production-considerations)

---

## Project Overview

Coaching institutes often manage fee information across desktop software, spreadsheets, phone calls and manual payment follow-ups. This can make it difficult for parents to check outstanding dues, for accounts teams to reconcile payments, and for management to review collections across centres.

FeeFlow provides a centralised workflow for:

- Maintaining a fee ledger for each student.
- Showing parents their linked student's fee and academic information.
- Recording and tracking instalment payments.
- Generating reminder events for upcoming and overdue instalments.
- Calculating a pro-rata refund estimate.
- Reviewing dues by centre, batch and ageing.
- Uploading attendance and test-score records in bulk.
- Exporting payment information for accounts reconciliation.
- Highlighting possible dropout risk for counsellor review.

The application has separate **Student**, **Parent** and **Accountant** entry points.

## Key Features

### 1. Role-based access

- **Student:** Uses a student demo access code to open the student portal.
- **Parent:** Uses a separate parent demo access code linked to a student.
- **Accountant:** Signs in using Supabase email/password authentication. The backend checks the authenticated user's role before granting access to accounts functionality.

### 2. Fee ledger and instalments

- Student fee plan and fee information.
- Instalment amounts, due dates and paid amounts.
- Outstanding balance and overdue information.
- Payment history associated with the student.

### 3. Parent portal

- Displays fee dues and instalment information for the linked student.
- Provides access to payment history and available receipts.
- Displays attendance and test-score information where records are available.
- Supports a mock instalment checkout workflow.

### 4. Payment links and mock checkout

- Creates a payment link for an instalment.
- Supports a simulated checkout confirmation.
- Updates the relevant instalment and payment records after mock confirmation.

> **Important:** The prototype's checkout simulates payment. It does not collect or transfer real money.

### 5. Automatic fee reminders

- Generates reminder events for eligible instalments.
- Supports English and Hindi reminder content.
- Skips fully paid instalments.
- Avoids creating duplicate reminder events for the same reminder stage.

> Reminder events are stored by the application. Live SMS, email or WhatsApp delivery requires a configured messaging provider and production integration.

### 6. Refund calculator

- Calculates a pro-rata refund estimate using the supplied course dates, fee and paid amount.
- Shows the elapsed course period, earned fee and estimated refund.

The calculation is a prototype implementation. The institute must confirm and approve its written refund policy before production use.

### 7. Accounts dashboard and exports

- Dues reporting grouped by centre and batch.
- Ageing information for outstanding instalments.
- Payment history and fee-ledger views.
- Tally-oriented payment CSV export.

The CSV export may require ledger and voucher mapping to match an institute's specific Tally configuration.

### 8. Bulk academic uploads

- Bulk attendance upload using CSV.
- Bulk test-score upload using CSV.
- Validates uploaded records against the expected columns and student records.

### 9. GST receipt PDFs

- Generates a downloadable payment receipt PDF for eligible successful payments.
- Uses institute GST configuration when supplied.

The institute's GST registration and tax treatment must be confirmed before treating a generated document as a tax invoice.

### 10. AI-assisted dropout-risk flags

- Reviews available instalment, attendance and test-score indicators.
- Produces a risk assessment for accounts/counsellor review.
- Allows staff to review a task or mark a flag as false.

AI output is advisory. It must not automatically change fees, initiate refunds or send messages to parents.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| Database | Supabase PostgreSQL |
| Accountant authentication | Supabase Auth |
| ORM | SQLAlchemy |
| API validation | Pydantic |
| AI risk assessment | OpenAI API |
| PDF receipts | ReportLab |
| Backend testing | pytest |

---

## Project Structure

The main project folders are organised as follows:

```text
coaching_system/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── jobs/
│   │   ├── models.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── ...
│   ├── package.json
│   └── .env
│
├── README.md
└── deployment.md
```

Some supporting files may be organised differently in the checked-out version. Use the actual repository structure as the source of truth.

---

## Requirements

Install the following before running the project:

- Python 3.10 or later (use the version supported by the project's dependencies).
- Node.js and npm.
- A Supabase project.
- Git.
- VS Code or another code editor (recommended).

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/prajjawal1707/coaching_system.git
cd coaching_system
```

### 2. Set up the backend

On Windows PowerShell:

```powershell
cd backend

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

If PowerShell prevents activation, use the appropriate execution-policy setting for your development environment or activate the virtual environment using Command Prompt:

```cmd
venv\Scripts\activate.bat
```

### 3. Set up the frontend

Open a second terminal:

```powershell
cd frontend
npm install
```

---

## Environment Configuration

Create the required local environment files. Do not commit real secrets to Git.

### Backend `.env`

The backend configuration uses environment variables for database access, authentication, admin-only demo-code generation, and optional integrations. Configure the variables expected by the checked-out backend code. These commonly include:

```env
DATABASE_URL=your_supabase_postgresql_connection_string

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

JWT_SECRET_KEY=replace_with_a_long_random_secret
DEMO_CODE_PEPPER=replace_with_a_long_random_secret
FEEFLOW_DEMO_ADMIN_KEY=replace_with_a_long_random_secret

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

FEEFLOW_INSTITUTE_NAME=Company A
FEEFLOW_INSTITUTE_ADDRESS=Jaipur, Rajasthan, India
FEEFLOW_GSTIN=
FEEFLOW_GST_RATE_PERCENT=
FEEFLOW_GST_INCLUSIVE=true
```

Only set variables for features you are configuring. Confirm exact variable names and required values in the backend source and deployment notes. Never share `.env` values publicly.

### Frontend `.env`

Set the frontend variables required by the Supabase client and API service in the checked-out source. For example, a Vite application commonly uses:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Use the exact variable names referenced by `frontend/src/services/` in your repository. Vite exposes variables prefixed with `VITE_` to browser code, so never put service-role keys, database passwords, admin keys or other secrets in frontend environment variables.

---

## Database Setup

1. Create or open the Supabase project.
2. Open **SQL Editor** in the Supabase Dashboard.
3. Run the database table and migration SQL supplied in `deployment.md` and the project setup notes.
4. Confirm that the schema matches the SQLAlchemy models in `backend/app/models.py`.
5. Configure Supabase Auth for the accountant account.
6. Add the required application user profile and role records.

Do not assume that creating the Supabase project automatically creates every application table. Apply the project's SQL setup before starting the application.

---

## Authentication and Demo Access

### Student login

Student access uses a dedicated demo code linked to a student record.

To generate a student code:

1. Start the backend.
2. Open `http://127.0.0.1:8000/docs`.
3. Find `POST /rbac/admin/students/{student_id}/generate-code`.
4. Select **Try it out** and enter the existing student ID, for example `FF-1001`.
5. Provide the admin key using the exact header configured in `backend/app/routes/rbac.py`.
6. Execute the request and securely copy the generated code from the response.
7. Select **Student** in the frontend and enter the code.

### Parent login

Parent access uses a separate demo code linked to the relevant student.

To generate a parent code:

1. Open `http://127.0.0.1:8000/docs`.
2. Find `POST /rbac/admin/students/{student_id}/generate-parent-code`.
3. Enter the existing student ID, for example `FF-1001`.
4. Supply a parent label if the endpoint requests one.
5. Provide the configured admin key using the exact header required by the backend.
6. Execute the request and securely copy the returned parent code.
7. Select **Parent** in the frontend and enter that parent code.

The parent code and student code are different credentials. Each should only grant access to the appropriate linked portal. The backend stores code hashes rather than plain-text codes.

### Accountant login

The accountant uses Supabase email/password authentication.

To provision an authorised accountant:

1. In Supabase Dashboard, open **Authentication → Users**.
2. Create or confirm the authorised user and set/reset the password.
3. Copy the user's Auth UUID.
4. Ensure a corresponding row exists in `public.user_profiles` with the role `accountant`.

For the schema described in the deployment guide, the role assignment query is:

```sql
INSERT INTO public.user_profiles (user_id, full_name, role)
VALUES ('REPLACE-WITH-AUTH-USER-UUID', 'Accounts Reviewer', 'accountant')
ON CONFLICT (user_id)
DO UPDATE SET
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role;
```

5. Select **Accountant** in the application and sign in using the registered email and password.

A successful Supabase login alone is not sufficient. The backend must also confirm the user's accountant role.

### OTP and mobile-number configuration

The parent and student prototype flows use demo access codes because the default email delivery service on the free Supabase setup has restrictive sending limits for repeated OTP testing.

Mobile-number OTP can be configured when the institute supplies authorised parent/student phone numbers and an SMS provider is configured in Supabase. Adding phone numbers alone does not enable OTP delivery. Production setup must also include phone verification, OTP expiry and retry limits, account recovery and appropriate consent.

**Do not publish passwords, demo codes, admin keys or API secrets in this README or in the public repository.** Share evaluator credentials separately through a private channel.

---

## Running the Application

### Start the backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Backend base URL:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Start the frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open the local URL printed by Vite in the terminal. The default Vite development URL is commonly:

```text
http://localhost:5173
```

Keep both development servers running while using the application.

---

## Running Tests

Run backend tests from the backend directory:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest -v
```

For a complete manual demonstration, verify:

- Student, parent and accountant role access.
- Fee ledger balances and instalment status.
- Parent payment-link creation and mock payment confirmation.
- Reminder generation, paid-instalment skipping and duplicate prevention.
- Refund calculations for representative course dates.
- Centre/batch dues reporting and ageing.
- Valid and invalid attendance/test-score CSV uploads.
- Payment receipt PDF generation.
- Tally-oriented payment CSV export.
- AI risk task generation, review and false-flag handling.

---

## Important API Workflows

The following routes are useful during development and evaluation. Check `/docs` for the exact request schema and required authentication.

| Workflow | Endpoint |
|---|---|
| Generate student demo code | `POST /rbac/admin/students/{student_id}/generate-code` |
| Generate parent demo code | `POST /rbac/admin/students/{student_id}/generate-parent-code` |
| Student demo login | `POST /rbac/student/login` |
| Parent demo login | `POST /rbac/parent/login` |
| Verify accountant access | `POST /rbac/accountant/verify` |
| Student portal data | `GET /rbac/student/portal` |
| Parent portal data | `GET /rbac/parent/portal` |
| Dues report | `GET /reports/dues` |
| Automatic reminder run | `POST /reminders/automatic/run` |
| Tally payment export | `GET /exports/tally/payments` |

Additional routes are available for students, instalments, payments, refunds, receipts, bulk uploads and counsellor tasks.

---

## Prototype Notes and Production Considerations

FeeFlow demonstrates the requested workflows as a working prototype. Before a live institute rollout, review and complete the following:

- **Payments:** Replace mock checkout with a payment gateway, signed server-to-server payment verification and reconciliation.
- **Reminders:** Configure a real email/SMS/WhatsApp provider, delivery status tracking, retries and suppression/cancellation rules.
- **Authentication:** Replace demo parent/student codes with a production OTP or approved identity flow, including verified phone numbers and secure recovery.
- **Authorisation:** Review role permissions and protect all sensitive routes and administrative provisioning operations.
- **Refunds:** Confirm the institute's approved written refund policy and validate the calculation against it.
- **GST:** Confirm the institute's GST registration, applicable rate and tax treatment before issuing tax invoices.
- **Student privacy:** Apply appropriate parental consent, data minimisation, retention and access controls for student/minor data.
- **Deployment:** Use HTTPS, production CORS settings, secure secret management, backups, logging, monitoring and database migration procedures.
- **Tally:** Validate exported voucher and ledger mappings against the institute's Tally configuration.

The AI dropout-risk feature is intended to support human review. It must not independently make fee decisions or contact parents.

---

## Project Submission Documents

The project handover package includes:

- `FeeFlow_Technical_Design_Document.docx` – technical design, architecture and implementation notes.
- `deployment.md` – deployment, database, authentication and testing instructions.

Refer to `deployment.md` for the detailed setup and handover procedure.

---

## Author / Repository

**Project:** FeeFlow – Coaching Institute Fee Management System  
**GitHub:** https://github.com/prajjawal1707/coaching_system
