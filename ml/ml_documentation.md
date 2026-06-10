# TrafficXShaper ML Service

## Service Overview and Operational Necessity

The primary function of the TrafficXShaper (TSX) Machine Learning (ML) Service is to predict future CPU utilization for client workloads to drive automated, proactive scaling actions.
By analyzing historical system metrics such as CPU usage, idle percentage, and active network connections, this service trains customized prediction models for each client. When scale-up or scale-down events are anticipated, the Decision Engine consumes these predictions to adjust virtual machine capacity. This predictive model helps prevent resource exhaustion before traffic peaks occur and avoids over-provisioning during quiet periods.

## Technology Stack

- **Web Framework**: FastAPI
- **Settings & Validation**: Pydantic and Pydantic Settings
- **Web Server Gateway**: Gunicorn (Process Manager) with Uvicorn (ASGI Workers)
- **Data Analysis & Modeling**: pandas, scikit-learn (RandomForestRegressor), joblib
- **HTTP Client**: requests with urllib3 Retry adapter
- **Virtualization**: Docker (utilizing python:3.11-slim base image)

## Technical Architecture and Component Analysis

- **main.py**
  Defines the FastAPI application and HTTP middleware. The middleware inspects incoming HTTP request headers for an 'X-Request-ID' trace header. If absent, it generates a unique UUID and attaches it to the request state and response headers to ensure end-to-end tracing across the system components. It also computes request processing duration and attaches it to the 'X-Process-Time' response header. It mounts routers for prediction, data insertion, model training, and health checks.

- **operations/prediction.py**
  Handles the core prediction logic. It defines the Pydantic validation schema `CleanMetrics` and exposes the `POST /prediction` endpoint. When a prediction request is received, it loads client-specific historical metrics from `file.csv` and the client's trained model (`model.pkl`). It generates feature lags, rolling mean, rolling standard deviation, and delta metrics based on a predefined feature order. The features are fed into the loaded Random Forest model to predict the next CPU value. The current request metrics are then asynchronously appended to the history file before returning the prediction.

- **operations/inserting.py**
  Exposes the `POST /insert` endpoint to record incoming system metrics without triggering a prediction. It validates metrics using `InsertMetrics` and uses the file helper to append the data to the client's CSV file.

- **operations/trigger_for_train.py**
  Exposes the `POST /train` endpoint to initiate model training. It takes a client ID and asynchronously triggers the training loop for that client's specific dataset.

- **train_model/train_model.py**
  Implements the model training pipeline. The `Train.train(client_id)` method reads the client's historical CSV dataset, constructs the target variable `cpu_next` (the shifted CPU value), generates lag and rolling features, splits the data sequentially (70% training, 15% validation, 15% testing), fits a `RandomForestRegressor` model (1000 estimators, max depth 7), and serializes the trained model as `model.pkl` in the client's directory.

- **setting/conifg.py**
  Uses Pydantic `BaseSettings` to load configurations from the local `.env` file, reading the log file paths (`LOG_FILE_PREDCITION`, `LOG_FILE_INSERTION`, `LOG_FILE_TRANNING`) and the base directory for client files (`FILE`).

- **setting/loggers.py**
  Implements a `LoggerFactory` to set up file logging for prediction, insertion, and training components, standardizing the log output format.

- **setting/session.py**
  Provides a retry-resilient requests session configured to retry failed HTTP requests (GET/POST) up to 5 times on 502, 503, and 504 status codes.

- **functions/supporters/file_handel.py**
  Contains utility class `File` with a static method `file_write` to safely append metric rows (CPU percentage, CPU idle percent, live connections) to the client's historical CSV data file.

- **health/health.py**
  Defines a basic `/health` route that returns `{"status": "ok"}` for service health monitoring.

- **Dockerfile**
  Configures the Docker container build starting from `python:3.11-slim`. It installs build dependencies (`gcc`, `make`), sets up a non-privileged user (`appuser`), creates appropriate logging and data directories, installs dependencies from `requirements.txt`, copies application source code, and starts the service using Gunicorn with Uvicorn workers on port 8000.

- **.env**
  Contains local configuration paths for application logs and user data:
  - `LOG_FILE_PREDCITION`: Log file path for prediction requests
  - `LOG_FILE_INSERTION`: Log file path for insertion requests
  - `LOG_FILE_TRANNING`: Log file path for model training logs
  - `FILE`: Base directory path for storing client data files and trained models
