# AI-Powered Natural Language Query System

A serverless AWS application that lets authenticated users ask questions in plain English, turn them into safe **read-only** SQL with **Amazon Bedrock**, and return results from **Amazon RDS** (MSSQL Server). The stack combines **Amazon Cognito**, **API Gateway**, **AWS Lambda**, and a small **React** client for demos and internal tools.

---

## Features

- **Natural language to SQL** via a **Bedrock Agent** (orchestrated from Lambda)
- **Defense in depth**: API Gateway **JWT** validation and throttling; Lambda-side **SELECT-only** validation and keyword blocking before touching the database
- **RDS as the source of truth** for structured data (e.g. football / player analytics workloads)
- **React (Vite)** web UI with Cognito sign-in and Bearer token calls to your API
- **Optional data utilities** in Python for loading CSV data and verifying database connectivity

---

## Architecture

The system follows an event-driven, serverless pattern on AWS: the client authenticates first, then calls a private API that chains Lambda functions from orchestration through validated query execution.



*Reference architecture: authentication, API edge, orchestration + AI, and read-only data access inside the network boundary.*

### Request flow

1. **Client** — User signs in; **Amazon Cognito** returns a **JWT**.
2. **API Gateway** — Client calls the API with `Authorization: Bearer <JWT>`; the gateway validates the token and applies **throttling** / usage plans as configured.
3. **Lambda (orchestrator)** — Receives the natural-language **query**, invokes **Amazon Bedrock** (e.g. agent / model) to produce candidate SQL, and coordinates the next step. **DynamoDB** is used in this pattern for metadata, schema catalogs, session or agent state—configure tables and IAM per your deployment.
4. **Lambda (validate & execute)** — Validates that only safe **SELECT** statements run, then queries **Amazon RDS** in **read-only** capacity (replica or read-only endpoint recommended for production).
5. **Response** — Results flow back through the orchestrator and API Gateway to the client.

---

## Tech stack


| Layer                       | Technology                                                                        |
| --------------------------- | --------------------------------------------------------------------------------- |
| Frontend                    | React 19, Vite 7, Amazon Cognito Identity JS                                      |
| API & auth                  | Amazon API Gateway, Amazon Cognito (JWT)                                          |
| Compute                     | AWS Lambda (Python)                                                               |
| AI                          | Amazon Bedrock (Agent Runtime in `lambda1`)                                       |
| Data                        | Amazon DynamoDB (metadata / orchestration, per design), Amazon RDS for SQL Server |
| Data access (worker Lambda) | `pymssql`                                                                         |


---

## Repository layout

```
├── docs/
│   └── architecture.png      # Architecture diagram (used by this README)
├── lambda1/
│   └── lambda_handler.py     # Orchestrator: Bedrock Agent → invoke SQL Lambda
├── lambda_container/
│   ├── lambda_function.py    # SELECT-only guardrails + RDS execution
│   ├── Dockerfile
│   └── requirements.txt
├── page/                     # Vite + React client
│   ├── .env.example
│   └── src/
├── load_player_data.py       # Load CSV into SQL Server (local / batch)
├── test_connection.py        # Verify ODBC connectivity (env-based)
└── check_tables.sql          # Sample data-quality check
```

---

## Configuration

### Orchestrator Lambda (`lambda1`)


| Variable         | Purpose                                          |
| ---------------- | ------------------------------------------------ |
| `AGENT_ID`       | Amazon Bedrock Agent ID                          |
| `AGENT_ALIAS_ID` | Bedrock Agent alias                              |
| `LAMBDA2_NAME`   | Name of the function that validates and runs SQL |


### SQL worker Lambda (`lambda_container`)


| Variable                  | Purpose                                                  |
| ------------------------- | -------------------------------------------------------- |
| `DB_HOST`                 | RDS hostname                                             |
| `DB_USER` / `DB_PASSWORD` | Database credentials (use Secrets Manager in production) |
| `DB_NAME`                 | Database name                                            |
| `DB_PORT`                 | Optional; defaults to `1433`                             |


### Web client (`page/`)

Copy `page/.env.example` to `page/.env` and set:


| Variable                    | Purpose                             |
| --------------------------- | ----------------------------------- |
| `VITE_COGNITO_USER_POOL_ID` | Cognito User Pool ID                |
| `VITE_COGNITO_CLIENT_ID`    | Cognito app client ID               |
| `VITE_API_BASE_URL`         | API Gateway invoke URL (stage)      |
| `VITE_API_PATH`             | Optional path segment (default `/`) |


### Local Python scripts

`load_player_data.py` expects `MSSQL_SERVER`, `MSSQL_DATABASE`, `MSSQL_USERNAME`, `MSSQL_PASSWORD` (see script headers). `test_connection.py` uses the same variables with **no defaults**, so credentials and host are never committed.

---

## Local development (frontend)

```bash
cd page
cp .env.example .env
# Edit .env with your Cognito and API Gateway values

npm install
npm run dev
```

Build for production:

```bash
npm run build
```

Host the `page/dist` output on S3/CloudFront or your preferred static host; ensure CORS and Cognito callback URLs match your deployment.
