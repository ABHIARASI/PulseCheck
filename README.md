
# PulseCheck — API Health Monitoring Dashboard

PulseCheck is a full-stack API monitoring application that checks endpoint availability, measures response time, records monitoring results, and displays API health through a React dashboard.

## Features

- **API health checks:** Send HTTP requests to monitor endpoints and classify their health.
- **Response time tracking:** Measure how long an endpoint takes to respond.
- **Automated monitoring:** Periodically check registered active monitors.
- **Monitoring history:** Store and display previous check results.
- **Dashboard summary:** View total checks, successful checks, failed checks, and check success rate.
- **Persistent storage:** Store monitors and results in PostgreSQL.
- **Automated tests:** Test API behavior using pytest and FastAPI TestClient.

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- HTTPX
- APScheduler

### Frontend
- React
- Vite
- JavaScript
- CSS

### Database and Testing
- PostgreSQL
- pytest
- FastAPI TestClient

## Architecture

1. The React frontend sends HTTP requests to the FastAPI backend.
2. FastAPI validates incoming requests and performs monitoring checks.
3. HTTPX sends requests to the monitored endpoints and measures response time.
4. SQLAlchemy stores monitor configurations and check results in PostgreSQL.
5. APScheduler periodically checks active monitors.
6. The dashboard retrieves monitor status, summary statistics, and monitoring history through API endpoints.

## Project Structure

```text
PulseCheck/
├── main.py
├── database.py
├── models.py
├── init_db.py
├── test_main.py
├── test_database.py
├── README.md
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── App.css
    └── package.json
```

## Prerequisites

- Python 3.13 or a compatible Python version
- Node.js and npm
- PostgreSQL
- A configured PostgreSQL database

## Backend Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the backend dependencies:

   ```powershell
   pip install fastapi uvicorn httpx sqlalchemy "psycopg[binary]" apscheduler pytest
   ```

3. Configure the PostgreSQL connection in `database.py`.

   Set `DATABASE_URL` to your local PostgreSQL connection string. Do not commit passwords or other secrets to GitHub.

4. Create the application tables:

   ```powershell
   python init_db.py
   ```

5. Start the backend:

   ```powershell
   python -m uvicorn main:app --reload
   ```

6. Open the interactive API documentation:

   http://127.0.0.1:8000/docs

## Frontend Setup

Open a separate terminal:

```powershell
cd frontend
npm install
npm install lucide-react
npm run dev
```

Open the local URL printed by Vite, usually:

http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Check whether the backend is running |
| POST | `/check` | Perform an individual API health check |
| GET | `/history` | Retrieve recent monitoring results |
| GET | `/summary` | Retrieve monitoring statistics |
| POST | `/monitors` | Register a monitor |
| GET | `/monitors` | List registered monitors |
| GET | `/monitors/{monitor_id}/latest` | Retrieve the latest result for a monitor |

### Example: Perform a Health Check

Request:

```json
{
  "url": "https://example.com"
}
```

Send it as a POST request to `/check`.

The response includes the URL, HTTP status code, response time, health classification, and check timestamp.

## Automated Testing

Run the tests from the project root:

```powershell
python -m pytest -v
```

The test suite covers:
- Backend startup and API documentation
- Healthy and unhealthy HTTP responses
- Connection failures and timeouts
- Duplicate monitor registration
- Invalid URL validation
- Summary fields and calculations

The project currently has 10 passing tests in the local development environment.

## Health Classification

- HTTP status codes from 200 through 399 are classified as healthy.
- HTTP status codes of 400 or above are classified as unhealthy.
- Connection errors and timeouts are recorded as unsuccessful checks.

The dashboard's success percentage represents the proportion of successful recorded checks, not a time-weighted uptime calculation.

## Limitations and Future Improvements

- Add monitor activation and deletion controls.
- Improve URL validation and protection against unsafe network targets.
- Add authentication and authorization before exposing the service publicly.
- Improve test isolation and dependency compatibility.
- Add charts, alerts, and configurable monitoring intervals.
- Add Docker-based deployment and CI testing.

## Security Note

This project is intended as a local demonstration. Do not expose it publicly without appropriate URL restrictions, authentication where needed, secret management, and deployment security controls.
