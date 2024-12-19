# Cellular Savior API

This is the backend API for Cellular Savior, a project designed to assist users in finding and comparing cellular plans.

**Note**: This repository is for demonstration purposes and is not intended for production use. Contact me for access to the production repository.

## Features

- OAuth 2.0 authentication with Google
- Plan recommendation system
- CRUD operations for cellular plans
- JWT-based user authorization

## Prerequisites

- A Google Cloud project set up with datastore and Google OAuth 2.0 authentication configured.
- Python installed on your system.

## Installation

1. Clone the repository:

    ```bash
    git clone [repository URL]
    ```

2. Navigate to the project directory:

    ```bash
    cd Cellular-Savior
    ```

3. Create a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. Set up environment variables required for the application. Create a `.env` file in the project root:

    ```env
    GOOGLE_AUTH_CLIENT_ID=your_google_client_id
    GOOGLE_AUTH_CLIENT_SECRET=your_google_client_secret
    PRIVATE_KEY=your_private_key
    PUBLIC_KEY=your_public_key
    ```
    *Note: Generate the keys with the function in the `utils` folder.*

2. Replace the placeholders with your actual Google OAuth 2.0 credentials and RSA keys.

## Running the Application

To start the application locally, run:

```bash
python main.py
```

## Testing the API

The API is available at `http://127.0.0.1:8080/api`.

Use `frontend_simulator.py` to simulate the frontend for testing and debugging purposes. This script simulates the Google OAuth flow, which isn't easily testable via Postman.

Run the "frontend" with the following command:

```bash
python frontend_simulator.py
```

The frontend simulator is available at `http://127.0.0.1:5000/`.

## API Endpoints

- `GET /api/auth/initiate`: Initiate OAuth 2.0 authentication.
- `POST /api/auth/callback`: Handle OAuth 2.0 callback.
- `GET /api/plans`: Retrieve all cellular plans.
- `POST /api/plans`: Create a new plan (Admin only).
- `GET /api/plans/<plan_id>`: Retrieve a specific plan.
- `PATCH /api/plans/<plan_id>`: Update a plan (Admin only).
- `DELETE /api/plans/<plan_id>`: Delete a plan (Admin only).
- `GET /api/recommend`: Get plan recommendations based on user input.



## A frontend repository will be released to interact with this API after it is deployed and sanitized.
