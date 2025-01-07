# Cellular Savior REST API

**[CellularSavior.com](https://cellularsavior.com)** is a web application designed to help users find the best cellular plan for their needs. By allowing users to compare plans, review detailed information, and receive personalized recommendations based on usage, **Cellular Savior** ultimately aims to provide a **trusted third-party** platform for both consumers and sales representatives to discuss **optimal cellular plans** with **transparency**.

Having worked in cellular sales for five years, I've seen firsthand how people are often taken advantage of—unnecessary fees, overpriced plans, and hidden contract terms are commonplace. **Cellular Savior** seeks to change that. Our goal is to **empower** individuals to make **informed decisions** while helping sales reps align with **honest sales practices**, cutting through the opacity and deceptive tactics that plague the market.

The application is built with Vue.js, Flask, and Google Cloud Platform (GAE, Datastore, OAuth 2.0).

You can find the frontend [here.](https://github.com/BByrge/Cell-Savior)

**Note**: This repository is for demonstration purposes and is not intended for production use. Contact me for access to the production repository.

## API Endpoints (you can use it at https://api.cellularsavior.com/)

- `GET /`: Retrieve the API docs.
- `GET /auth/initiate`: Initiate OAuth 2.0 authentication.
- `POST /auth/callback`: Handle OAuth 2.0 callback.
- `GET /auth/key`: Get public key for JWT verification.
- `GET /auth/verifyjwt`: Verify JWT token.
- `GET /plans`: Retrieve all cellular plans.
- `POST /plans`: Create a new plan (Admin only).
- `GET /plans/<plan_id>`: Retrieve a specific plan.
- `PATCH /plans/<plan_id>`: Update a plan (Admin only).
- `DELETE /plans/<plan_id>`: Delete a plan (Admin only).
- `POST /recommend`: Get plan recommendations based on user input.

## Features

- OAuth 2.0 authentication with Google
- Plan recommendation system
- CRUD operations for cellular plans
- JWT-based user authorization

## Upcoming Features

- Side-by-side plan comparison
- Sales rep tools
- Articles and guides


# Installation (for whatever reason)

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

