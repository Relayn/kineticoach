# 🏋️ KinetiCoach: Your AI Fitness Assistant

KinetiCoach is a Full-Stack application in the form of a Telegram Mini App that analyzes your squat technique in real-time and provides instant audio-visual feedback.

This project is designed to showcase skills in real-time systems, computer vision, and modern full-stack development.

## 🛠️ Tech Stack

| Category          | Backend (Python) | Frontend (React) |
| :---------------- | :--------------- | :--------------- |
| **Framework**     | FastAPI          | React            |
| **Language**      | Python 3.11+     | TypeScript       |
| **Real-Time**     | WebSockets       | WebSockets       |
| **Computer Vision**| MediaPipe        | -                |
| **Quality Tools** | `ruff`, `mypy`, `pytest` | `eslint`, `prettier`, `jest` |
| **Deployment**    | Docker           | Docker           |

## 🚀 Getting Started

> **Note:** The project is under active development.

To run the entire application locally, you will need Docker and Docker Compose installed.

1.  Clone the repository.
2.  Create and configure your `.env` file in the `backend` directory based on `.env.example`.
3.  Run the application:
    ```bash
    docker-compose up --build
    ```

## Project Structure

```
kineticoach/
├── backend/          # Python/FastAPI application
│   ├── src/
│   ├── tests/
│   ├── .env.example
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/         # React/TypeScript Mini App (coming soon)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── .github/          # CI/CD workflows
├── docker-compose.yml
└── README.md         # You are here
