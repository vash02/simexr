# SimExR API Reference

## 🎯 Quick Navigation

- [Authentication](#authentication)
- [Health Check APIs](#health-check-apis)
- [Simulation APIs](#simulation-apis)
- [Reasoning APIs](#reasoning-apis)
- [Database APIs](#database-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## 🔐 Authentication

Currently, SimExR API uses OpenAI API key authentication configured in the system. No additional API authentication is required for the SimExR endpoints themselves.

**Configuration:**
```yaml
# config.yaml
openai:
  api_key: "your-openai-api-key-here"
```

---

## 🏥 Health Check APIs

### `GET /health/status`

**Description:** Get comprehensive system health status

**Response Model:** `HealthResponse`

**Example Request:**
```bash
curl -X GET "http://localhost:8000/health/status"
```

**Example Response:**
```json
{
  "status": "healthy",
  "components": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection successful",
      "last_check": "2024-01-15T10:30:00Z"
    },
    {
      "name": "simulation_execution",
      "status": "healthy",
      "message": "Simulation execution working",
      "last_check": "2024-01-15T10:30:00Z"
    },
    {
      "name": "models_directory",
      "status": "healthy",
      "message": "Models directory accessible, 45 models found",
      "last_check": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200`: System is healthy
- `503`: System has health issues

---

### `POST /health/test`

**Description:** Run comprehensive system tests

**Request Model:** `TestRequest`

**Response Model:** `TestResponse`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/health/test" \
  -H "Content-Type: application/json" \
  -d '{
    "test_type": "end_to_end",
    "parameters": {
      "test_write": true
    }
  }'
```

**Available Test Types:**
- `simulation`: Test simulation execution
- `database`: Test database operations
- `reasoning`: Test reasoning agent (mock)
- `end_to_end`: Complete workflow test

**Example Response:**
```json
{
  "test_type": "end_to_end",
  "success": true,
  "message": "End-to-end test completed successfully",
  "details": {
    "model_created": "e2e_test_model_abc123",
    "simulation_success": true,
    "results_stored": true,
    "cleanup_completed": true
  },
  "execution_time": 2.45
}
```

---

## 🔬 Simulation APIs

### `POST /simulation/transform/github`

**Description:** Import and transform GitHub scripts into standardized simulation functions

**Request Body:**
```json
{
  "github_url": "string",
  "model_name": "string",
  "max_smoke_iters": 3
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/simulation/transform/github" \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
    "model_name": "vanderpol_transformed",
    "max_smoke_iters": 3
  }'
```

**Example Response:**
```json
{
  "status": "success",
  "model_id": "vanderpol_transformed_eac8429aea8f",
  "message": "Successfully transformed script from GitHub",
  "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
  "model_name": "vanderpol_transformed",
  "script_path": "external_models/vanderpol_transformed.py",
  "script_content": "def simulate(mu=1.0, z0=[2, 0], eval_time=20, t_iteration=1000, plot=False):\n    # Transformed code here\n    return results",
  "metadata": {
    "parameters": {
      "mu": "Damping parameter",
      "z0": "Initial conditions",
      "eval_time": "Simulation time",
      "t_iteration": "Number of time steps",
      "plot": "Enable plotting"
    }
  }
}
```

**Status Codes:**
- `200`: Successfully transformed
- `500`: Transformation failed

---

### `POST /simulation/run`

**Description:** Execute a single simulation with specified parameters

**Request Model:** `SingleSimulationRequest`

**Response Model:** `SimulationResult`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/simulation/run" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "vanderpol_transformed_eac8429aea8f",
    "parameters": {
      "mu": 1.5,
      "z0": [2.0, 0.0],
      "eval_time": 20,
      "t_iteration": 1000,
      "plot": false
    }
  }'
```

**Example Response:**
```json
{
  "success": true,
  "parameters": {
    "mu": 1.5,
    "z0": [2.0, 0.0],
    "eval_time": 20,
    "t_iteration": 1000,
    "plot": false
  },
  "results": {
    "time": [0.0, 0.02, 0.04, "..."],
    "x": [2.0, 1.98, 1.94, "..."],
    "y": [0.0, -0.15, -0.28, "..."],
    "max_x": 2.1,
    "min_x": -2.1,
    "period_estimate": 6.28,
    "data_points": 1000
  },
  "execution_time": 0.067,
  "stdout": "Van der Pol simulation completed successfully",
  "stderr": "",
  "error_message": null
}
```

**Status Codes:**
- `200`: Simulation successful
- `404`: Model not found
- `422`: Invalid parameters
- `500`: Execution failed

---

### `POST /simulation/batch`

**Description:** Execute multiple simulations with different parameter sets

**Request Model:** `BatchSimulationRequest`

**Response Model:** `BatchSimulationResponse`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/simulation/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "vanderpol_transformed_eac8429aea8f",
    "parameter_grid": [
      {
        "mu": 1.0,
        "z0": [2.0, 0.0],
        "eval_time": 20,
        "t_iteration": 1000
      },
      {
        "mu": 1.5,
        "z0": [2.0, 0.0],
        "eval_time": 20,
        "t_iteration": 1000
      },
      {
        "mu": 2.0,
        "z0": [2.0, 0.0],
        "eval_time": 20,
        "t_iteration": 1000
      }
    ]
  }'
```

**Example Response:**
```json
{
  "status": "completed",
  "total_runs": 3,
  "successful_runs": 3,
  "failed_runs": 0,
  "results": [
    {
      "success": true,
      "parameters": {"mu": 1.0, "z0": [2.0, 0.0], "eval_time": 20, "t_iteration": 1000},
      "results": {"time": [...], "x": [...], "y": [...], "max_x": 2.0, "min_x": -2.0},
      "execution_time": 0.065,
      "stdout": "Simulation completed",
      "stderr": "",
      "error_message": null
    },
    "... additional results ..."
  ],
  "execution_time": 0.234
}
```

**Constraints:**
- Maximum batch size: 1000 simulations
- Individual simulation timeout: 30 seconds

---

### `GET /simulation/models`

**Description:** List all available simulation models

**Query Parameters:**
- None

**Example Request:**
```bash
curl -X GET "http://localhost:8000/simulation/models"
```

**Example Response:**
```json
{
  "status": "success",
  "count": 45,
  "models": [
    {
      "id": "vanderpol_transformed_eac8429aea8f",
      "name": "vanderpol_transformed",
      "metadata": {
        "description": "Van der Pol oscillator simulation",
        "parameters": {
          "mu": "Damping parameter",
          "z0": "Initial conditions"
        }
      },
      "script_path": "external_models/vanderpol_transformed.py",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "... additional models ..."
  ]
}
```

---

### `GET /simulation/models/search`

**Description:** Search models using fuzzy matching

**Query Parameters:**
- `name` (required): Search term
- `limit` (optional): Maximum results (default: 20, max: 100)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/simulation/models/search?name=pendulum&limit=5"
```

**Example Response:**
```json
{
  "status": "success",
  "search_term": "pendulum",
  "total_matches": 8,
  "returned_count": 5,
  "limit": 5,
  "models": [
    {
      "id": "simple_pendulum_abc123",
      "name": "Simple Pendulum",
      "metadata": {
        "description": "Basic pendulum simulation",
        "parameters": {
          "length": "Pendulum length",
          "gravity": "Gravitational acceleration",
          "angle0": "Initial angle"
        }
      }
    },
    "... additional matches ..."
  ]
}
```

**Search Algorithm:**
- Exact matches get highest priority
- Partial matches in name/ID
- Word boundary matches
- Relevance scoring applied

---

### `GET /simulation/models/{model_id}`

**Description:** Get detailed information about a specific model

**Path Parameters:**
- `model_id`: Model identifier

**Example Request:**
```bash
curl -X GET "http://localhost:8000/simulation/models/vanderpol_transformed_eac8429aea8f"
```

**Example Response:**
```json
{
  "status": "success",
  "model": {
    "id": "vanderpol_transformed_eac8429aea8f",
    "name": "vanderpol_transformed",
    "metadata": {
      "description": "Van der Pol oscillator simulation",
      "parameters": {
        "mu": "Damping parameter (default: 1.0)",
        "z0": "Initial conditions (default: [2, 0])",
        "eval_time": "Simulation time (default: 20)",
        "t_iteration": "Number of time steps (default: 1000)",
        "plot": "Enable plotting (default: False)"
      },
      "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
      "transformation_date": "2024-01-15T10:30:00Z"
    },
    "script_path": "external_models/vanderpol_transformed.py",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### `GET /simulation/models/{model_id}/results`

**Description:** Get simulation results for a specific model

**Path Parameters:**
- `model_id`: Model identifier

**Query Parameters:**
- `limit` (optional): Maximum results (default: 100)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/simulation/models/vanderpol_transformed_eac8429aea8f/results?limit=10&offset=0"
```

**Example Response:**
```json
{
  "status": "success",
  "total_count": 150,
  "limit": 10,
  "offset": 0,
  "model_id": "vanderpol_transformed_eac8429aea8f",
  "results": [
    {
      "parameters": {
        "mu": 1.5,
        "z0": [2.0, 0.0],
        "eval_time": 20,
        "t_iteration": 1000
      },
      "results": {
        "time": [...],
        "x": [...],
        "y": [...],
        "max_x": 2.1,
        "min_x": -2.1,
        "period_estimate": 6.28
      },
      "timestamp": "2024-01-15T10:30:00Z",
      "execution_time": 0.067
    },
    "... additional results ..."
  ]
}
```

---

### `DELETE /simulation/models/{model_id}/results`

**Description:** Clear all simulation results for a specific model

**Path Parameters:**
- `model_id`: Model identifier

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/simulation/models/vanderpol_transformed_eac8429aea8f/results"
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Deleted 150 results for model vanderpol_transformed_eac8429aea8f",
  "deleted_count": 150
}
```

---

### `GET /simulation/models/{model_id}/script`

**Description:** Get the simulation script content

**Path Parameters:**
- `model_id`: Model identifier

**Example Request:**
```bash
curl -X GET "http://localhost:8000/simulation/models/vanderpol_transformed_eac8429aea8f/script"
```

**Example Response:**
```json
{
  "status": "success",
  "model_id": "vanderpol_transformed_eac8429aea8f",
  "script": "def simulate(mu=1.0, z0=[2, 0], eval_time=20, t_iteration=1000, plot=False):\n    \"\"\"\n    Van der Pol oscillator simulation\n    \"\"\"\n    import numpy as np\n    from scipy.integrate import odeint\n    \n    def vanderpol(z, t, mu):\n        x, y = z\n        dzdt = [y, mu*(1 - x**2)*y - x]\n        return dzdt\n    \n    t = np.linspace(0, eval_time, t_iteration)\n    sol = odeint(vanderpol, z0, t, args=(mu,))\n    \n    return {\n        'time': t.tolist(),\n        'x': sol[:, 0].tolist(),\n        'y': sol[:, 1].tolist(),\n        'max_x': float(np.max(sol[:, 0])),\n        'min_x': float(np.min(sol[:, 0])),\n        'period_estimate': estimate_period(sol[:, 0], t)\n    }",
  "script_path": "external_models/vanderpol_transformed.py",
  "is_placeholder": false
}
```

---

### `POST /simulation/models/{model_id}/script`

**Description:** Save modified script content

**Path Parameters:**
- `model_id`: Model identifier

**Request Body:**
```json
{
  "script": "def simulate(**params):\n    # Modified script content\n    return results"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/simulation/models/vanderpol_transformed_eac8429aea8f/script" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def simulate(mu=1.0, z0=[2, 0], eval_time=20, t_iteration=1000, plot=False):\n    # Modified van der Pol implementation\n    import numpy as np\n    # ... implementation\n    return results"
  }'
```

**Example Response:**
```json
{
  "status": "success",
  "model_id": "vanderpol_transformed_eac8429aea8f",
  "message": "Script saved successfully for model vanderpol_transformed_eac8429aea8f",
  "script_path": "external_models/vanderpol_transformed.py"
}
```

---

## 🧠 Reasoning APIs

### `POST /reasoning/ask`

**Description:** Ask AI reasoning questions about simulation data

**Request Model:** `ReasoningRequest`

**Response Model:** `ReasoningResponse`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/reasoning/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "vanderpol_transformed_eac8429aea8f",
    "question": "How does the damping parameter mu affect the oscillation behavior? Analyze the relationship between mu and the period of oscillation.",
    "max_steps": 10
  }'
```

**Example Response:**
```json
{
  "answer": "Based on my analysis of the van der Pol oscillator simulation data:\n\n**Effect of Damping Parameter μ on Oscillation Behavior:**\n\n1. **μ < 1 (Weak nonlinearity)**: The system exhibits nearly sinusoidal oscillations with small amplitude variations. The period is close to 2π.\n\n2. **μ ≈ 1 (Moderate nonlinearity)**: Clear limit cycle behavior emerges with characteristic relaxation oscillations. The period increases slightly.\n\n3. **μ > 1 (Strong nonlinearity)**: The oscillations become increasingly \"square-wave\" like with sharp transitions and flat regions. The period increases significantly.\n\n**Quantitative Analysis:**\n- For μ = 0.5: Period ≈ 6.3 seconds\n- For μ = 1.0: Period ≈ 6.7 seconds  \n- For μ = 1.5: Period ≈ 7.8 seconds\n- For μ = 2.0: Period ≈ 9.2 seconds\n\n**Key Relationship:** Period ≈ 2π(1 + μ²/16) for moderate μ values\n\nThe data shows a clear positive correlation between μ and oscillation period, with the relationship becoming more nonlinear for larger μ values.",
  "model_id": "vanderpol_transformed_eac8429aea8f",
  "question": "How does the damping parameter mu affect the oscillation behavior?",
  "history": [
    {
      "role": "user",
      "content": "How does the damping parameter mu affect the oscillation behavior?"
    },
    {
      "role": "assistant", 
      "content": "I'll analyze the van der Pol oscillator data to understand the effect of the damping parameter μ. Let me start by examining the available data..."
    },
    {
      "role": "tool",
      "name": "python_exec",
      "content": "# Load and examine the simulation data\ndf = load_results()\nprint(f\"Dataset shape: {df.shape}\")\nprint(f\"Available columns: {list(df.columns)}\")\nprint(f\"μ parameter range: {df['mu'].min()} to {df['mu'].max()}\")"
    }
  ],
  "code_map": {
    "1": "df_mu_analysis = df.groupby('mu').agg({'period_estimate': ['mean', 'std'], 'max_x': 'mean'})",
    "2": "plt.figure(figsize=(10, 6))\nplt.scatter(df['mu'], df['period_estimate'], alpha=0.6)\nplt.xlabel('Damping parameter μ')\nplt.ylabel('Period (seconds)')",
    "3": "correlation = df[['mu', 'period_estimate']].corr().iloc[0,1]\nprint(f'Correlation between μ and period: {correlation:.3f}')"
  },
  "images": ["mu_period_relationship.png", "phase_portraits_comparison.png"],
  "execution_time": 73.4
}
```

**Request Parameters:**
- `model_id`: Must exist in database with simulation results
- `question`: Natural language question (1-1000 characters)
- `max_steps`: Reasoning steps limit (1-50, default: 20)

**Response Features:**
- Comprehensive natural language answer
- Complete conversation history
- Code execution map with numbered snippets
- Generated visualization images
- Execution time tracking

---

### `GET /reasoning/history/{model_id}`

**Description:** Get reasoning conversation history for a model

**Path Parameters:**
- `model_id`: Model identifier

**Query Parameters:**
- `limit` (optional): Maximum conversations (default: 50, max: 200)
- `offset` (optional): Skip conversations (default: 0)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/reasoning/history/vanderpol_transformed_eac8429aea8f?limit=10&offset=0"
```

**Example Response:**
```json
{
  "status": "success",
  "total_count": 25,
  "limit": 10,
  "offset": 0,
  "history": [
    {
      "id": "conv_abc123",
      "model_id": "vanderpol_transformed_eac8429aea8f",
      "question": "How does the damping parameter mu affect oscillation behavior?",
      "answer": "Based on my analysis of the van der Pol oscillator...",
      "images": ["mu_period_relationship.png"],
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "conv_def456", 
      "model_id": "vanderpol_transformed_eac8429aea8f",
      "question": "What is the stability of the limit cycle?",
      "answer": "The van der Pol oscillator exhibits a stable limit cycle...",
      "images": ["stability_analysis.png"],
      "timestamp": "2024-01-15T09:15:00Z"
    },
    "... additional conversations ..."
  ]
}
```

---

### `DELETE /reasoning/history/{model_id}`

**Description:** Clear all reasoning history for a specific model

**Path Parameters:**
- `model_id`: Model identifier

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/reasoning/history/vanderpol_transformed_eac8429aea8f"
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Deleted 25 reasoning conversations for model vanderpol_transformed_eac8429aea8f",
  "deleted_count": 25
}
```

---

### `GET /reasoning/conversations`

**Description:** Get all reasoning conversations across all models

**Query Parameters:**
- `limit` (optional): Maximum conversations (default: 100)
- `offset` (optional): Skip conversations (default: 0)
- `model_id` (optional): Filter by specific model

**Example Request:**
```bash
curl -X GET "http://localhost:8000/reasoning/conversations?limit=20&model_id=vanderpol_transformed_eac8429aea8f"
```

**Example Response:**
```json
{
  "status": "success",
  "total_count": 173,
  "limit": 20,
  "offset": 0,
  "conversations": [
    {
      "id": "conv_latest",
      "model_id": "vanderpol_transformed_eac8429aea8f",
      "question": "Compare behavior at different mu values",
      "answer": "The van der Pol oscillator shows distinct behavioral regimes...",
      "images": ["comparison_plot.png"],
      "timestamp": "2024-01-15T11:45:00Z"
    },
    "... additional conversations ..."
  ]
}
```

---

### `GET /reasoning/stats`

**Description:** Get reasoning usage statistics

**Example Request:**
```bash
curl -X GET "http://localhost:8000/reasoning/stats"
```

**Example Response:**
```json
{
  "status": "success",
  "overall": {
    "total_conversations": 173,
    "unique_models": 18,
    "first_conversation": "2024-01-10T08:00:00Z",
    "last_conversation": "2024-01-15T11:45:00Z"
  },
  "per_model": [
    {
      "model_id": "vanderpol_transformed_eac8429aea8f",
      "conversation_count": 25,
      "first_conversation": "2024-01-12T10:00:00Z",
      "last_conversation": "2024-01-15T11:45:00Z"
    },
    {
      "model_id": "lorenz_system_xyz789",
      "conversation_count": 18,
      "first_conversation": "2024-01-11T14:30:00Z", 
      "last_conversation": "2024-01-15T09:20:00Z"
    },
    "... additional models ..."
  ]
}
```

---

## 🗄️ Database APIs

### `POST /database/models`

**Description:** Store a new simulation model in the database

**Request Model:** `StoreModelRequest`

**Response Model:** `StoreModelResponse`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/database/models" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "custom_oscillator",
    "metadata": {
      "description": "Custom harmonic oscillator",
      "parameters": {
        "omega": "Angular frequency",
        "damping": "Damping coefficient",
        "amplitude": "Initial amplitude"
      },
      "author": "Research Team",
      "version": "1.0",
      "tags": ["oscillator", "dynamics", "custom"]
    },
    "script_content": "def simulate(omega=1.0, damping=0.1, amplitude=1.0, time_span=10, **kwargs):\n    import numpy as np\n    from scipy.integrate import odeint\n    \n    def oscillator(y, t, omega, damping):\n        x, v = y\n        dydt = [v, -2*damping*v - omega**2*x]\n        return dydt\n    \n    t = np.linspace(0, time_span, 1000)\n    y0 = [amplitude, 0]\n    sol = odeint(oscillator, y0, t, args=(omega, damping))\n    \n    return {\n        \"time\": t.tolist(),\n        \"position\": sol[:, 0].tolist(),\n        \"velocity\": sol[:, 1].tolist(),\n        \"energy\": (0.5 * sol[:, 1]**2 + 0.5 * omega**2 * sol[:, 0]**2).tolist()\n    }"
  }'
```

**Example Response:**
```json
{
  "model_id": "custom_oscillator_def789ghi",
  "status": "success",
  "message": "Model custom_oscillator stored successfully"
}
```

---

### `POST /database/models/upload`

**Description:** Upload a simulation model from a file

**Request Parameters:**
- `model_name` (form field): Name of the model
- `metadata` (form field): JSON string with model metadata
- `script_file` (file): Python script file (.py)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/database/models/upload" \
  -F "model_name=uploaded_model" \
  -F "metadata={\"description\": \"Uploaded simulation\", \"author\": \"User\"}" \
  -F "script_file=@my_simulation.py"
```

**Example Response:**
```json
{
  "model_id": "uploaded_model_jkl012mno",
  "status": "success", 
  "message": "Model uploaded_model uploaded successfully"
}
```

**File Requirements:**
- Must be a Python file (.py extension)
- Must contain a `simulate(**params)` function
- Maximum file size: 10MB

---

### `GET /database/models`

**Description:** List all models in the database

**Query Parameters:**
- `limit` (optional): Maximum models (default: 100)
- `offset` (optional): Skip models (default: 0)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/database/models?limit=20&offset=0"
```

**Example Response:**
```json
{
  "status": "success",
  "total_count": 45,
  "limit": 20,
  "offset": 0,
  "models": [
    {
      "id": "vanderpol_transformed_eac8429aea8f",
      "name": "vanderpol_transformed",
      "metadata": {
        "description": "Van der Pol oscillator simulation",
        "parameters": {...},
        "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py"
      },
      "script_path": "external_models/vanderpol_transformed.py",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "... additional models ..."
  ]
}
```

---

### `GET /database/models/{model_id}`

**Description:** Get detailed information about a specific model

**Path Parameters:**
- `model_id`: Model identifier

**Example Request:**
```bash
curl -X GET "http://localhost:8000/database/models/vanderpol_transformed_eac8429aea8f"
```

**Example Response:**
```json
{
  "status": "success",
  "model": {
    "id": "vanderpol_transformed_eac8429aea8f",
    "name": "vanderpol_transformed",
    "metadata": {
      "description": "Van der Pol oscillator simulation",
      "parameters": {
        "mu": "Damping parameter (default: 1.0)",
        "z0": "Initial conditions (default: [2, 0])",
        "eval_time": "Simulation time (default: 20)",
        "t_iteration": "Number of time steps (default: 1000)"
      },
      "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
      "transformation_date": "2024-01-15T10:30:00Z"
    },
    "script_path": "external_models/vanderpol_transformed.py",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "statistics": {
    "total_simulation_runs": 150,
    "first_run": "2024-01-15T10:35:00Z",
    "last_run": "2024-01-15T11:45:00Z",
    "reasoning_conversations": 25
  }
}
```

---

### `DELETE /database/models/{model_id}`

**Description:** Delete a model and all associated data

**Path Parameters:**
- `model_id`: Model identifier

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/database/models/old_model_abc123"
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Model old_model_abc123 deleted successfully",
  "deleted_results": 75,
  "deleted_conversations": 12
}
```

**Warning:** This operation permanently deletes:
- Model metadata and script
- All simulation results
- All reasoning conversations
- Associated files

---

### `GET /database/results`

**Description:** Get simulation results across all or specific models

**Query Parameters:**
- `model_id` (optional): Filter by specific model
- `limit` (optional): Maximum results (default: 100, max: 10000)
- `offset` (optional): Skip results (default: 0)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/database/results?model_id=vanderpol_transformed_eac8429aea8f&limit=50"
```

**Example Response:**
```json
{
  "status": "success",
  "total_count": 150,
  "limit": 50,
  "offset": 0,
  "model_id": "vanderpol_transformed_eac8429aea8f",
  "results": [
    {
      "model_id": "vanderpol_transformed_eac8429aea8f",
      "parameters": {
        "mu": 1.5,
        "z0": [2.0, 0.0],
        "eval_time": 20,
        "t_iteration": 1000
      },
      "results": {
        "time": [...],
        "x": [...],
        "y": [...],
        "max_x": 2.1,
        "min_x": -2.1,
        "period_estimate": 6.28
      },
      "timestamp": "2024-01-15T10:30:00Z",
      "execution_time": 0.067
    },
    "... additional results ..."
  ]
}
```

**Data Processing:**
- NaN values are automatically converted to null for JSON compatibility
- Large arrays may be truncated in responses
- Results are ordered by timestamp (newest first)

---

### `GET /database/stats`

**Description:** Get comprehensive database statistics

**Example Request:**
```bash
curl -X GET "http://localhost:8000/database/stats"
```

**Example Response:**
```json
{
  "status": "success",
  "database": {
    "path": "/path/to/mcp.db",
    "size_mb": 15.7
  },
  "models": {
    "total": 45,
    "first_created": "2024-01-10T08:00:00Z",
    "last_created": "2024-01-15T11:30:00Z"
  },
  "results": {
    "total": 2847,
    "models_with_results": 38,
    "first_result": "2024-01-10T08:15:00Z",
    "last_result": "2024-01-15T11:45:00Z"
  },
  "reasoning": {
    "total_conversations": 173,
    "models_with_conversations": 18,
    "first_conversation": "2024-01-10T09:00:00Z",
    "last_conversation": "2024-01-15T11:45:00Z"
  }
}
```

---

### `POST /database/backup`

**Description:** Create a backup of the database

**Example Request:**
```bash
curl -X POST "http://localhost:8000/database/backup"
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Database backup created successfully",
  "backup_path": "/path/to/mcp.db.backup_20240115_114500",
  "backup_size_mb": 15.7,
  "timestamp": "20240115_114500"
}
```

**Backup Features:**
- Automatic timestamp in filename
- Complete database copy
- Preserves all data integrity
- Returns backup file information

---

## ⚠️ Error Handling

### Standard Error Response Format

All API endpoints return errors in a consistent format:

```json
{
  "detail": "Error description",
  "error_type": "ValidationError|NotFoundError|ExecutionError|SystemError",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123def456"
}
```

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| `200` | Success | Request completed successfully |
| `400` | Bad Request | Invalid request format or parameters |
| `404` | Not Found | Model, result, or resource not found |
| `422` | Validation Error | Pydantic model validation failed |
| `500` | Internal Server Error | System error, execution failure |
| `503` | Service Unavailable | System health check failed |

### Error Examples

#### 404 - Model Not Found
```json
{
  "detail": "Model nonexistent_model_123 not found",
  "error_type": "NotFoundError",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 422 - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "parameters", "mu"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "error_type": "ValidationError",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 500 - Execution Error
```json
{
  "detail": "Simulation failed: NameError: name 'undefined_variable' is not defined",
  "error_type": "ExecutionError",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Handling Best Practices

1. **Always check status codes** before processing responses
2. **Parse error details** for specific error information
3. **Implement retry logic** for 5xx errors
4. **Validate inputs** before sending requests
5. **Handle timeouts** for long-running operations

---

## 🚦 Rate Limiting

### Current Limits

| Endpoint Category | Requests per Minute | Notes |
|------------------|-------------------|-------|
| Health Check | 60 | Lightweight operations |
| Simulation Execution | 30 | Resource-intensive operations |
| AI Reasoning | 10 | LLM API rate limits apply |
| Database Operations | 120 | Read operations higher limit |

### Rate Limit Headers

Responses include rate limiting information:

```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1642248000
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "error_type": "RateLimitError",
  "retry_after": 45,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 📝 Request/Response Examples

### Complete Workflow Example

```bash
#!/bin/bash
# Complete SimExR workflow example

# 1. Check system health
echo "=== Checking System Health ==="
curl -s "http://localhost:8000/health/status" | jq '.status'

# 2. Import model from GitHub
echo "=== Importing Model ==="
MODEL_RESPONSE=$(curl -s -X POST "http://localhost:8000/simulation/transform/github" \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
    "model_name": "workflow_demo",
    "max_smoke_iters": 3
  }')

MODEL_ID=$(echo $MODEL_RESPONSE | jq -r '.model_id')
echo "Model ID: $MODEL_ID"

# 3. Run single simulation
echo "=== Running Single Simulation ==="
curl -s -X POST "http://localhost:8000/simulation/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"model_id\": \"$MODEL_ID\",
    \"parameters\": {
      \"mu\": 1.5,
      \"z0\": [2.0, 0.0],
      \"eval_time\": 20,
      \"t_iteration\": 1000
    }
  }" | jq '.success'

# 4. Run batch simulations
echo "=== Running Batch Simulations ==="
curl -s -X POST "http://localhost:8000/simulation/batch" \
  -H "Content-Type: application/json" \
  -d "{
    \"model_id\": \"$MODEL_ID\",
    \"parameter_grid\": [
      {\"mu\": 1.0, \"z0\": [2.0, 0.0], \"eval_time\": 20, \"t_iteration\": 1000},
      {\"mu\": 1.5, \"z0\": [2.0, 0.0], \"eval_time\": 20, \"t_iteration\": 1000},
      {\"mu\": 2.0, \"z0\": [2.0, 0.0], \"eval_time\": 20, \"t_iteration\": 1000}
    ]
  }" | jq '.successful_runs'

# 5. Ask AI reasoning question
echo "=== AI Analysis ==="
curl -s -X POST "http://localhost:8000/reasoning/ask" \
  -H "Content-Type: application/json" \
  -d "{
    \"model_id\": \"$MODEL_ID\",
    \"question\": \"How does the mu parameter affect the oscillation period?\",
    \"max_steps\": 8
  }" | jq -r '.answer' | head -n 5

echo "=== Workflow Complete ==="
```

### Python Client Example

```python
import requests
import json
import time

class SimExRClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check system health."""
        response = self.session.get(f"{self.base_url}/health/status")
        response.raise_for_status()
        return response.json()
    
    def import_from_github(self, github_url, model_name, max_smoke_iters=3):
        """Import and transform GitHub script."""
        data = {
            "github_url": github_url,
            "model_name": model_name,
            "max_smoke_iters": max_smoke_iters
        }
        response = self.session.post(
            f"{self.base_url}/simulation/transform/github",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def run_simulation(self, model_id, parameters):
        """Run single simulation."""
        data = {
            "model_id": model_id,
            "parameters": parameters
        }
        response = self.session.post(
            f"{self.base_url}/simulation/run",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def run_batch_simulation(self, model_id, parameter_grid):
        """Run batch simulations."""
        data = {
            "model_id": model_id,
            "parameter_grid": parameter_grid
        }
        response = self.session.post(
            f"{self.base_url}/simulation/batch",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def ask_reasoning_question(self, model_id, question, max_steps=20):
        """Ask AI reasoning question."""
        data = {
            "model_id": model_id,
            "question": question,
            "max_steps": max_steps
        }
        response = self.session.post(
            f"{self.base_url}/reasoning/ask",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_results(self, model_id=None, limit=100, offset=0):
        """Get simulation results."""
        params = {"limit": limit, "offset": offset}
        if model_id:
            params["model_id"] = model_id
        
        response = self.session.get(
            f"{self.base_url}/database/results",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == "__main__":
    client = SimExRClient()
    
    # Check health
    health = client.health_check()
    print(f"System status: {health['status']}")
    
    # Import model
    import_result = client.import_from_github(
        "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
        "python_client_demo"
    )
    model_id = import_result["model_id"]
    print(f"Imported model: {model_id}")
    
    # Run simulation
    sim_result = client.run_simulation(
        model_id,
        {"mu": 1.5, "z0": [2.0, 0.0], "eval_time": 20, "t_iteration": 1000}
    )
    print(f"Simulation success: {sim_result['success']}")
    
    # Ask AI question
    reasoning_result = client.ask_reasoning_question(
        model_id,
        "What is the period of oscillation for mu=1.5?"
    )
    print(f"AI Answer: {reasoning_result['answer'][:200]}...")
```

---

## 📚 Additional Resources

### OpenAPI Specification

The complete OpenAPI specification is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **JSON Schema**: `http://localhost:8000/openapi.json`

### SDK and Libraries

- **Python Client**: See example above
- **JavaScript/Node.js**: Available on request
- **R Package**: In development
- **MATLAB Toolbox**: Planned

### Support and Community

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Complete guides and tutorials
- **Examples**: Sample scripts and notebooks
- **Community**: Discussion forums and chat

---

*This API reference is automatically generated from the FastAPI application. For the most up-to-date information, please refer to the interactive documentation at `/docs`.*
