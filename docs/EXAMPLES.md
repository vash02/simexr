# Examples & Demonstrations

Real-world examples of using SimExR for scientific simulations.

## 🌊 Van der Pol Oscillator

### Complete Workflow Example

```bash
# 1. Import from GitHub
curl -X POST "http://localhost:8000/simulation/transform/github" \
  -d '{
    "github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
    "model_name": "vanderpol_demo"
  }'

# 2. Run parameter sweep
curl -X POST "http://localhost:8000/simulation/batch" \
  -d '{
    "model_id": "vanderpol_demo_abc123",
    "parameter_grid": [
      {"mu": 1.0, "z0": [2,0], "eval_time": 20},
      {"mu": 1.5, "z0": [2,0], "eval_time": 20},
      {"mu": 2.0, "z0": [2,0], "eval_time": 20}
    ]
  }'

# 3. AI Analysis
curl -X POST "http://localhost:8000/reasoning/ask" \
  -d '{
    "model_id": "vanderpol_demo_abc123",
    "question": "How does mu affect the oscillation period?"
  }'
```

## 🌀 Lorenz Attractor

### Chaos Analysis Example

```python
import requests

# Import Lorenz system
response = requests.post("http://localhost:8000/simulation/transform/github", json={
    "github_url": "https://github.com/user/lorenz.py",
    "model_name": "lorenz_chaos"
})
model_id = response.json()["model_id"]

# Parameter sweep for chaos transition
parameter_grid = []
for rho in [20, 24, 28, 32, 36]:
    parameter_grid.append({
        "sigma": 10,
        "rho": rho,
        "beta": 8/3,
        "initial": [1, 1, 1],
        "time_span": 50
    })

# Run batch simulation
batch_response = requests.post("http://localhost:8000/simulation/batch", json={
    "model_id": model_id,
    "parameter_grid": parameter_grid
})

# Analyze chaos transition
reasoning_response = requests.post("http://localhost:8000/reasoning/ask", json={
    "model_id": model_id,
    "question": "At what rho value does the system transition to chaos? Analyze the Lyapunov exponents.",
    "max_steps": 15
})

print(reasoning_response.json()["answer"])
```

## 🔬 Custom Simulation

### Creating Your Own Model

```python
# custom_oscillator.py
def simulate(omega=1.0, damping=0.1, amplitude=1.0, time_span=10, **kwargs):
    """Custom damped harmonic oscillator."""
    import numpy as np
    from scipy.integrate import odeint
    
    def oscillator(y, t, omega, damping):
        x, v = y
        dydt = [v, -2*damping*v - omega**2*x]
        return dydt
    
    t = np.linspace(0, time_span, 1000)
    y0 = [amplitude, 0]
    sol = odeint(oscillator, y0, t, args=(omega, damping))
    
    return {
        "time": t.tolist(),
        "position": sol[:, 0].tolist(),
        "velocity": sol[:, 1].tolist(),
        "energy": (0.5 * sol[:, 1]**2 + 0.5 * omega**2 * sol[:, 0]**2).tolist()
    }
```

Upload and use:
```bash
# Upload custom model
curl -X POST "http://localhost:8000/database/models/upload" \
  -F "model_name=custom_oscillator" \
  -F "metadata={\"description\": \"Custom harmonic oscillator\"}" \
  -F "script_file=@custom_oscillator.py"

# Run with different parameters
curl -X POST "http://localhost:8000/simulation/run" \
  -d '{
    "model_id": "custom_oscillator_xyz789",
    "parameters": {"omega": 2.0, "damping": 0.2, "amplitude": 1.5}
  }'
```

## 📊 Data Analysis Workflow

### Python Client Example

```python
class SimExRAnalysis:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def complete_analysis(self, github_url, model_name, questions):
        """Complete analysis workflow."""
        # Import model
        import_response = requests.post(f"{self.base_url}/simulation/transform/github", json={
            "github_url": github_url,
            "model_name": model_name
        })
        model_id = import_response.json()["model_id"]
        
        # Generate parameter grid
        parameter_grid = self.generate_parameter_grid()
        
        # Run batch simulation
        batch_response = requests.post(f"{self.base_url}/simulation/batch", json={
            "model_id": model_id,
            "parameter_grid": parameter_grid
        })
        
        # Ask multiple questions
        insights = []
        for question in questions:
            reasoning_response = requests.post(f"{self.base_url}/reasoning/ask", json={
                "model_id": model_id,
                "question": question,
                "max_steps": 12
            })
            insights.append({
                "question": question,
                "answer": reasoning_response.json()["answer"],
                "images": reasoning_response.json().get("images", [])
            })
        
        return {
            "model_id": model_id,
            "batch_results": batch_response.json(),
            "insights": insights
        }
    
    def generate_parameter_grid(self):
        """Generate systematic parameter grid."""
        import itertools
        import numpy as np
        
        # Example for van der Pol oscillator
        mu_values = np.linspace(0.5, 3.0, 6)
        initial_conditions = [[1, 0], [2, 0], [1, 1]]
        
        grid = []
        for mu, ic in itertools.product(mu_values, initial_conditions):
            grid.append({
                "mu": float(mu),
                "z0": ic,
                "eval_time": 20,
                "t_iteration": 1000
            })
        
        return grid

# Usage
analyzer = SimExRAnalysis()
results = analyzer.complete_analysis(
    "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py",
    "comprehensive_analysis",
    [
        "What is the relationship between mu and oscillation period?",
        "How do initial conditions affect the final attractor?",
        "What are the stability properties of the limit cycle?",
        "Can you identify any bifurcation points?"
    ]
)

# Process results
for insight in results["insights"]:
    print(f"Q: {insight['question']}")
    print(f"A: {insight['answer'][:200]}...")
    print(f"Generated {len(insight['images'])} visualizations")
    print("-" * 50)
```

## 🎯 Advanced Use Cases

### Multi-Model Comparison

```bash
# Import multiple models
models=("vanderpol.py" "duffing.py" "lorenz.py")
model_ids=()

for model in "${models[@]}"; do
    response=$(curl -s -X POST "http://localhost:8000/simulation/transform/github" \
        -d "{\"github_url\": \"https://github.com/user/$model\", \"model_name\": \"${model%.py}\"}")
    model_id=$(echo $response | jq -r '.model_id')
    model_ids+=($model_id)
done

# Run comparative analysis
for model_id in "${model_ids[@]}"; do
    curl -X POST "http://localhost:8000/reasoning/ask" \
        -d "{\"model_id\": \"$model_id\", \"question\": \"Characterize the dynamical behavior and identify key features\"}"
done
```

### Automated Parameter Optimization

```python
def parameter_optimization(model_id, target_metric, parameter_ranges):
    """Automated parameter optimization using simulation results."""
    import numpy as np
    from scipy.optimize import minimize
    
    def objective_function(params):
        # Convert params to parameter dict
        param_dict = dict(zip(parameter_ranges.keys(), params))
        
        # Run simulation
        response = requests.post("http://localhost:8000/simulation/run", json={
            "model_id": model_id,
            "parameters": param_dict
        })
        
        if response.json()["success"]:
            results = response.json()["results"]
            return abs(results.get(target_metric, float('inf')))
        else:
            return float('inf')
    
    # Define bounds
    bounds = [(r["min"], r["max"]) for r in parameter_ranges.values()]
    
    # Initial guess
    x0 = [(r["min"] + r["max"]) / 2 for r in parameter_ranges.values()]
    
    # Optimize
    result = minimize(objective_function, x0, bounds=bounds, method='L-BFGS-B')
    
    return {
        "optimal_parameters": dict(zip(parameter_ranges.keys(), result.x)),
        "optimal_value": result.fun,
        "success": result.success
    }

# Example usage
optimization_result = parameter_optimization(
    "vanderpol_demo_abc123",
    "period_estimate",  # Target: minimize period
    {
        "mu": {"min": 0.1, "max": 2.0},
        "eval_time": {"min": 10, "max": 50}
    }
)
```

[← Back to Documentation](index.md)
