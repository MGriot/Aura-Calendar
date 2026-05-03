# Running the Web Application

Aura Calendar is split into a modern React/Vite frontend and a FastAPI Python backend. Both can be run together using Docker Compose or separately in local development mode.

## 1. Running with Docker Compose (Recommended)

The easiest way to start the entire application is via Docker Compose.

1. Make sure Docker and Docker Compose are installed on your machine.
2. From the root directory of the project, run:
   ```bash
   docker-compose up --build
   ```

This will build the images and start the containers.
- The **Frontend** will be accessible at: `http://localhost:5173`
- The **Backend API** will be accessible at: `http://localhost:8000`

## 2. Running Locally for Development

If you prefer to run the components directly on your host machine without Docker:

### Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI application using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
The frontend application will typically be accessible at `http://localhost:5173`. It will proxy or directly call the backend on port 8000 (ensure the backend is running simultaneously).
