# Google Maps Data Extraction Suite
**Professional Edition | User Guide v1.0**

## 1. System Requirements

Before installing the software, ensure the following environments are installed on your machine:

- **Python 3.10 or higher**: Required for the backend engine. [Download Python](https://www.python.org/downloads/)
- **Node.js 18 or higher**: Required for the user interface. [Download Node.js](https://nodejs.org/)
- **Google Chrome**: Required for the browser automation engine.

## 2. Installation Guide

Open your terminal or command prompt and navigate to the extracted project folder.

### Step A: Backend Setup
Install the necessary Python dependencies.

```bash
# Navigate to root folder
pip install -r backend/requirements.txt
```

### Step B: Frontend Setup
Install the interface dependencies.

```bash
cd frontend
npm install
cd ..
```

## 3. Launching the Application

To start the suite (Backend, Worker, and Interface) simultaneously, run the startup script:

**macOS / Linux:**
```bash
chmod +x run_app.sh
./run_app.sh
```

**Windows:**
You may need to run the backend and frontend in separate terminals if you do not have a bash environment enabled.
- Terminal 1: `python -m uvicorn backend.main:app --reload`
- Terminal 2: `python -m backend.worker`
- Terminal 3: `cd frontend && npm run dev:electron`

## 4. Operational Workflow

### Defining Target Areas
1. Use the **Polygon Tool** (top right of map) to draw a specific search zone.
2. You can draw multiple disjointed zones to target different neighborhoods simultaneously.

### Setting Search Parameters
1. Click the **Search** button (top left floating panel).
2. Enter your keywords (e.g., "Coffee Shops," "Real Estate Agents") and hit Enter to add them.
3. Select the keywords you want to run for this session.

### Execution
1. Click **START EXTRACTION** at the bottom of the screen.
2. The system will slice the geographic area into intelligent sub-grids to ensure maximum coverage.
3. Monitor progress via the **Jobs Dashboard** sidebar tab.

### Data Export
1. Navigate to the **Jobs** tab.
2. Once a job shows "Completed" or "Processing", click **Download**.
3. Select your preferred format (Excel, CSV, JSON).
4. Enable **Normalize Phone Numbers** to automatically format contact details to strict E.164 standards (e.g., `+15550001234`).

## 5. Configuration & Intelligence

**System Intelligence Tab**
This software enables external selection logic updates. If Google Maps changes its layout, update `backend/scraper/selectors.json` or use the "Check for Updates" button in Settings > System Intelligence to simulate pulling new definitions without reinstalling the software.

**Performance Tuning**
In Settings > Performance, you can adjust:
- **Concurrency**: Number of simultaneous browser agents. (Recommended: 2-3 for standard laptops).
- **Request Delay**: Time between actions. Higher delay reduces ban risk.

## 6. Troubleshooting

**Map Tiles Not Loading**
Ensure you have an active internet connection. The system uses CartoDB Dark Matter tiles which require online access.

**Browser Errors / 0 Results**
- Check your internet connection.
- Verify you are not behind a strict corporate firewall blocking automated traffic.
- If using Proxies, verify their status in `backend/core/proxies.py` or the configuration file.

---
© 2026 Google Maps Data Extraction Suite. All rights reserved.
