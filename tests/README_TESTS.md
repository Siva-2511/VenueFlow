# 🧪 VenueFlow AI — Testing Suite
This project implements a rigorous testing framework using `pytest` to ensure 100% stability and reliability of the crowd management logic.

## 📊 Test Suite Overview
We have implemented **13 test cases** across two specialized modules:

### 1. `tests/test_app.py` (Core Business Logic)
- **Gate Assignment Algorithm**: Verifies that new users are automatically routed to the gate with the lowest live load (Load Balancing).
- **Authentication Security**: 
  - Validates PBKDF2 hashing during login.
  - Ensures session integrity and protection of restricted routes.
- **D1 Database Integration**: Mocks SQL responses to verify robust data persistence and retrieval.
- **WebSocket Broadcasts**: Ensures real-time events are correctly triggered upon ticket scanning.

### 2. `tests/test_gemini.py` (AI Service Reliability)
- **Strategic Advice Retrieval**: Mocks the Gemini 2.5 API to verify that the system correctly processes and displays tactical recommendations.
- **Graceful Failure Handling**: 
  - Ensures the UI provides a professional fallback when the API key is missing.
  - Tests "Protective Cooling" logic for 429 (Resource Exhausted) scenarios.
- **Safety Filter Validation**: Confirms that the AI agent adheres to the system's strict security instructions (never providing passwords/hashes).

---

## 🛠️ How to Run Tests
To execute the full suite and verify the platform's stability:

1.  **Ensure dependencies are installed**:
    ```bash
    pip install pytest pytest-flask pytest-mock
    ```

2.  **Run the suite (Auto-discovery enabled via `pytest.ini`)**:
    ```bash
    pytest
    ```

3.  **View Verbose Output**:
    ```bash
    pytest -v
    ```

---

## ✅ Current Status
- **Total Tests**: 13
- **Passed**: 13
- **Failed**: 0
- **Coverage**: Core Logistics, AI Services, Authentication, and Real-time Synchronization.
