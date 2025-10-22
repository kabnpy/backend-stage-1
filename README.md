# String Analyzer Service (HNG13 - Stage 1)

This project implements a RESTful API service using **Python** and **FastAPI** to analyze strings and compute their properties (length, palindrome status, word count, hash, etc.).

The **SHA-256 hash** of the string is used as the unique identifier (`id`) and key for the in-memory database.

## Technology Stack

*   **Language:** Python 3.10+
*   **Framework:** FastAPI
*   **Server:** Uvicorn (ASGI server)
*   **Storage:** In-Memory Dictionary (Non-persistent)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kabnpy/backend-stage-1.git
    cd backend-stage-1
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To run the application locally, use the following command:
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. Interactive documentation can be found at `http://127.0.0.1:8000/docs`.

## API Endpoints

| Method | Endpoint                               | Description                                                                 |
|--------|----------------------------------------|-----------------------------------------------------------------------------|
| POST   | `/strings`                             | Analyze and store a new string.                                             |
| GET    | `/strings/{string_value}`              | Retrieve a specific string by its original value (via hash lookup).         |
| GET    | `/strings`                             | Retrieve all strings with structured query filtering (e.g., `?is_palindrome=true`). |
| GET    | `/strings/filter-by-natural-language`  | Retrieve strings using a plain text query (e.g., `?query=all single word`). |
| DELETE | `/strings/{string_value}`              | Delete a specific string by its original value.                             |

