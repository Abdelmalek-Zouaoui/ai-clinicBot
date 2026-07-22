# 🏥 Clinic Management System (`ai-clinicBot`)

A modern, highly responsive, and AI-powered clinic management desktop application built using Python with **CustomTkinter** for a premium GUI, and **SQLite** for secure database storage. The system features a native multi-threaded AI medical assistant and a data analyst engine powered by the **Groq LLM API** (`llama-3.3-70b-versatile`).

This system is fully localized, supporting real-time language switching between **English**, **French**, and **Arabic**.

---

## 🔄 Transition & Entity Mapping
This project has been refactored from a Pharmacy Management system to a dedicated Clinic Management System. The mapping between original pharmacy terms and new clinic entities is as follows:

| Pharmacy Entity | Clinic Entity | Description |
| :--- | :--- | :--- |
| **Medicine** | ➡️ **Service** | Consultation, clinical services, medical examinations, or operations. |
| **Supplier** | ➡️ **Patient** | Patient profiles, contact details, medical history, and records. |
| **Sales / POS** | ➡️ **Appointment / Visit** | Check-ins, waitlists, billing of services, and checkouts. |
| **Sale Items** | ➡️ **Appointment Services + Rx** | Specific services billed for a visit and prescribed medicines. |

---

## 🌟 Key Features

### 🖥️ 1. Modern Admin Dashboard
* **Dynamic KPIs**: Instant statistics for today's waitlist queue, completed visits, revenue generated, and total registered patients.
* **Interactive Data Visualization**: Real-time revenue charts displaying month-over-month clinic trends.
* **Waitlist Queue**: High-level snapshot of active, pending, or checked-out patients waiting for consultation.

### 🤖 2. Advanced AI Assistant Agent (`ai-core`)
* **Multi-Step Agent Loop**: Leverages function calling (tools) without heavy frameworks (like LangChain) to query the SQLite database directly.
* **Natural Language Queries**: Search patients by name/phone/email, fetch full patient records (medical history, prescription lists), and schedule new appointments directly through chat.
* **Medical Helpers**:
  * **Patient Summarizer**: Condenses a patient's historical medical records and consultation notes into a concise brief for the physician.
  * **Diagnostic Suggester**: Recommends potential diagnoses and alert signs based on a patient's chief complaints.
* **Thread-Safe Worker Execution (`AIWorker`)**: AI operations run in background threads to keep the CustomTkinter GUI completely fluid and responsive.

### 📊 3. Automated Dashboard Insights
* **Deterministic Metrics**: A dedicated SQLite analytics engine evaluates month-over-month patient attendance, busiest days/hours, service popularity, and revenue.
* **Actionable Advice**: Metrics are formatted and processed by the LLM to generate prioritized optimization insights (e.g., advising campaigns to recall patients due for a 60-day checkup, or rescheduling staff during peak hours).

### 👥 4. Comprehensive Patient Management
* Comprehensive profiles: full name, date of birth, gender, blood type, phone, email, wilaya (state), address, allergies, and permanent medical history.
* Quick lookup: Live, debounced search filters for patients by name or phone numbers.

### 🩺 5. Services & Prescriptions
* **Services**: Manage clinical services (prices, duration, category, description, preview images).
* **Prescriptions**: Prescribe medicines and notes during appointments, and generate printable PDF templates via **ReportLab**.

### 🌍 6. Dynamic Localization
* Instant, runtime language switching:
  * **English (`en`)**
  * **French (`fr`)**
  * **Arabic (`ar`)** (supporting RTL structures)

### 🛡️ 7. Self-Healing Database & Backups
* SQLite integrity verification on startup.
* Automatic recovery: if the database file is corrupted, the application automatically restores the latest verified backup.
* Manual and automatic daily backup scheduling via `BackupManager`.

---

## 📁 Project Directory Structure

```text
clinic_app/
├── ai-core/                    # AI Agent Engine & SQL Analytics
│   ├── ai_worker.py            # Thread-safe background execution wrapper for LLM calls
│   ├── clinic_analytics.py     # SQL metrics calculation (busiest hours, revenue change)
│   └── llm_service.py          # Groq LLM integration, function calling tools, prompts
│
├── database/                   # SQLite database storage & backup folders
│   ├── backups/                # Local automated backup snapshots
│   └── clinic.db               # Active database file
│
├── model/                      # Data Access Layer & Business Logic Models
│   ├── appointment_model.py    # Appointment scheduling, checkout, queue statistics
│   ├── db_manager.py           # SQLite connection wrapper with execute/fetch helpers
│   ├── patient_model.py        # Patient CRUD, validation, and search queries
│   ├── prescription_model.py   # Prescriptions logging & report mapping
│   ├── service_model.py        # Medical services registry & lookup
│   └── user_model.py           # Employee management, authentication, Bcrypt passwords
│
├── view/                       # Presentation Layer (CustomTkinter GUI Views)
│   ├── admin/                  # Admin-only dashboard tabs & management views
│   │   ├── add_service.py      # New service registry form (with photo preview)
│   │   ├── alert_list_view.py  # Critical clinic notifications and warnings
│   │   ├── appointment_view.py # Front-desk appointment scheduling & billing page
│   │   ├── dashboard.py        # Main stats, waitlist, revenue graph, and AI insights panel
│   │   ├── export_view.py      # Reports export (PDF receipts, Excel sheets)
│   │   ├── patient_view.py     # Patient roster and detailed records manager
│   │   ├── prescription_view.py# Physician's prescription creator
│   │   ├── service_list.py     # Services pricing list view
│   │   ├── settings_view.py    # General clinic metadata configuration & backup tools
│   │   ├── user_mgmt.py        # Staff accounts and access levels (Admin / Employee)
│   │   └── waiting_room_view.py# Live status display of patient queue
│   ├── ai_window.py            # Floating chat box for the AI assistant
│   ├── login_view.py           # Secure credentials verification page
│   └── sidebar.py              # Collapsible navigation side panel
│
├── prescriptions/              # Generated PDF prescriptions ready for printing
│├── utils/                     # Miscellaneous helpers
│   └── backup_manager.py       # Symlink or replica helper for backup utilities
│
├── .env                        # Configuration secrets (API keys)
├── backup_manager.py           # Core database backup controller
├── localization.py             # Language translation key mapping (ar / fr / en)
├── main.py                     # Main application entry point (controller bootstrapping)
└── requirements.txt            # Project dependencies list
```

---

## 🛠️ Technology Stack
* **Language**: Python 3.9+
* **GUI Engine**: CustomTkinter
* **Assets / Images**: Pillow (PIL)
* **Encryption**: Bcrypt
* **PDF Engine**: ReportLab
* **Excel Engine**: Openpyxl
* **LLM Engine**: Groq Python SDK (using model `llama-3.3-70b-versatile`)
* **Environment variables**: Python-dotenv
* **Database**: SQLite3

---

## 🚀 Installation & Setup

### 1. Clone & Navigate to Project Directory
```bash
git clone https://github.com/Abdelmalek-Zouaoui/ai-clinicBot.git
cd clinic_app
```

### 2. Install Dependencies
Ensure you have Python installed, then install the required libraries:
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory and add your Groq API Key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Launch Application
Start the system by running the main entry script:
```bash
python main.py
```
* **Default Admin Credentials**:
  * **Username**: `admin`
  * **Password**: `admin123`

---

## 🔒 Security & Performance
* **Bcrypt Password Hashing**: Avoids plaintext storage of user passwords in `clinic.db`.
* **Database Integrity Self-Check**: Runs `PRAGMA integrity_check` on launch. In case of disk write failures or physical file corruption, the `BackupManager` restores the most recent stable configuration silently.
* **GUI Responsiveness**: The app uses non-blocking multi-threaded processing (`threading.Thread` with daemon mode) for any API or file IO operations, keeping CustomTkinter frames running at a smooth 60fps.
