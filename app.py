import json
import requests
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
import streamlit as st
from streamlit_chat import message
import time
import numpy as np

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────

def make_display_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert complex data types in DataFrame to display-safe strings."""
    display_df = df.copy()
    
    for col in display_df.columns:
        if display_df[col].dtype == 'object':
            # Get a sample non-null value to check the type
            non_null_values = display_df[col].dropna()
            if not non_null_values.empty:
                sample_val = non_null_values.iloc[0]
                
                # Handle different complex types
                if isinstance(sample_val, dict):
                    # Convert dict to JSON string
                    display_df[col] = display_df[col].apply(
                        lambda x: json.dumps(x, default=str) if isinstance(x, dict) else str(x)
                    )
                elif isinstance(sample_val, (list, tuple)):
                    # Convert list/tuple to string representation
                    display_df[col] = display_df[col].apply(
                        lambda x: str(x) if isinstance(x, (list, tuple)) else str(x)
                    )
                elif isinstance(sample_val, np.complexfloating) or (hasattr(sample_val, 'real') and hasattr(sample_val, 'imag')):
                    # Handle complex numbers
                    display_df[col] = display_df[col].apply(
                        lambda x: f"{x.real:.6f}+{x.imag:.6f}j" if hasattr(x, 'real') and hasattr(x, 'imag') else str(x)
                    )
                elif isinstance(sample_val, np.ndarray):
                    # Handle numpy arrays
                    display_df[col] = display_df[col].apply(
                        lambda x: f"array(shape={x.shape}, dtype={x.dtype})" if isinstance(x, np.ndarray) else str(x)
                    )
                else:
                    # Convert everything else to string
                    display_df[col] = display_df[col].astype(str)
    
    return display_df

# ─────────────────────────────────────────────────────────────────────
# API Helper Functions
# ─────────────────────────────────────────────────────────────────────

def make_api_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    """Make an API request and return the response."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            if params:
                # Use query parameters for POST requests that expect them
                response = requests.post(url, headers=headers, params=params)
            else:
                # Use JSON body for POST requests that expect JSON
                response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return {"error": str(e)}

def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        result = make_api_request("GET", "/health/status")
        return "error" not in result
    except:
        return False

def search_models(query: str, limit: int = 10) -> List[Dict]:
    """Search for models using the fuzzy search API with caching."""
    cache_key = f"{query}_{limit}"
    
    # Check cache first
    if cache_key in st.session_state.cached_search_results:
        return st.session_state.cached_search_results[cache_key]
    
    # Fetch from API
    result = make_api_request("GET", f"/simulation/models/search?name={query}&limit={limit}")
    models = result.get("models", []) if "error" not in result else []
    
    # Cache the results
    st.session_state.cached_search_results[cache_key] = models
    return models

def get_model_info(model_id: str) -> Dict:
    """Get detailed information about a model with caching."""
    # Check cache first
    if model_id in st.session_state.cached_model_info:
        return st.session_state.cached_model_info[model_id]
    
    # Fetch from API
    result = make_api_request("GET", f"/simulation/models/{model_id}")
    model_info = result.get("model", {}) if "error" not in result else {}
    
    # Cache the results
    if model_info:
        st.session_state.cached_model_info[model_id] = model_info
    
    return model_info

def get_model_results(model_id: str, limit: int = 100) -> Dict:
    """Get simulation results for a model with caching."""
    cache_key = f"{model_id}_{limit}"
    
    # Check cache first
    if cache_key in st.session_state.cached_model_results:
        return st.session_state.cached_model_results[cache_key]
    
    # Fetch from API
    result = make_api_request("GET", f"/simulation/models/{model_id}/results?limit={limit}")
    
    # Cache the results
    if "error" not in result:
        st.session_state.cached_model_results[cache_key] = result
    
    return result if "error" not in result else {}

def ask_reasoning_question(model_id: str, question: str, max_steps: int = 5) -> Dict:
    """Ask a question to the reasoning agent."""
    data = {
        "model_id": model_id,
        "question": question,
        "max_steps": max_steps
    }
    result = make_api_request("POST", "/reasoning/ask", data)
    return result if "error" not in result else {}

def get_reasoning_history(model_id: str, limit: int = 10) -> List[Dict]:
    """Get reasoning conversation history for a model."""
    result = make_api_request("GET", f"/reasoning/history/{model_id}?limit={limit}")
    return result.get("conversations", []) if "error" not in result else []

def get_model_script(model_id: str) -> str:
    """Get the refactored script for a model."""
    result = make_api_request("GET", f"/simulation/models/{model_id}/script")
    return result.get("script", "") if "error" not in result else ""

def save_model_script(model_id: str, script: str) -> Dict:
    """Save the modified script for a model."""
    data = {"script": script}
    result = make_api_request("POST", f"/simulation/models/{model_id}/script", data)
    return result if "error" not in result else {}

def clear_model_cache(model_id: str = None):
    """Clear cache for a specific model or all models."""
    if model_id:
        # Clear specific model cache
        if model_id in st.session_state.cached_model_info:
            del st.session_state.cached_model_info[model_id]
        
        # Clear all cached results for this model
        keys_to_remove = [key for key in st.session_state.cached_model_results.keys() if key.startswith(model_id)]
        for key in keys_to_remove:
            del st.session_state.cached_model_results[key]
        
        # Clear model code cache
        if model_id in st.session_state.cached_model_code:
            del st.session_state.cached_model_code[model_id]
    else:
        # Clear all cache
        st.session_state.cached_model_info.clear()
        st.session_state.cached_model_results.clear()
        st.session_state.cached_model_code.clear()
        st.session_state.cached_search_results.clear()

def refresh_model_data(model_id: str):
    """Force refresh of model data by clearing cache and re-fetching."""
    clear_model_cache(model_id)
    return get_model_info(model_id)

def store_simulation_results(model_id: str, results: Dict[str, Any], result_type: str = "single"):
    """Store simulation results for a model with metadata."""
    import time
    
    st.session_state.model_simulation_results[model_id] = {
        "results": results,
        "timestamp": time.time(),
        "type": result_type,  # "single" or "batch"
        "model_id": model_id
    }
    st.session_state.last_simulation_model = model_id
    st.session_state.simulation_results = results  # Keep backward compatibility

def get_cached_simulation_results(model_id: str = None) -> Optional[Dict[str, Any]]:
    """Get cached simulation results for a model."""
    if model_id and model_id in st.session_state.model_simulation_results:
        return st.session_state.model_simulation_results[model_id]
    elif st.session_state.last_simulation_model:
        # Return results from the last simulation if no specific model requested
        return st.session_state.model_simulation_results.get(st.session_state.last_simulation_model)
    return None

def display_cached_results_banner():
    """Display a banner if there are cached simulation results."""
    if st.session_state.last_simulation_model:
        cached_data = get_cached_simulation_results()
        if cached_data:
            model_id = cached_data["model_id"]
            result_type = cached_data.get("type", "single")
            timestamp = cached_data.get("timestamp", 0)
            
            # Format timestamp
            import datetime
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            
            st.info(f"💾 **Cached Results Available**: {result_type.title()} simulation from model `{model_id}` (Run at {time_str})")
            
            if st.button("📊 View Cached Results"):
                st.session_state.selected_model_id = model_id
                # Display results inline
                with st.expander("📊 Latest Simulation Results", expanded=True):
                    results = cached_data["results"]
                    
                    if result_type == "batch" and "results" in results:
                        st.success(f"✅ Batch Results: {len(results['results'])} simulations")
                        
                        # Convert to DataFrame for better display
                        try:
                            df = pd.json_normalize(results["results"], sep=".")
                            display_df = make_display_safe(df)
                            st.dataframe(display_df, use_container_width=True)
                        except Exception as e:
                            st.json(results)
                    else:
                        st.success("✅ Single Simulation Results")
                        st.json(results)

def cache_view_results(model_id: str, df: pd.DataFrame, metadata: Dict[str, Any]):
    """Cache the DataFrame and metadata for the View Results page."""
    st.session_state.view_results_model_id = model_id
    st.session_state.view_results_dataframe = df
    st.session_state.view_results_metadata = metadata

def get_cached_view_results() -> tuple:
    """Get cached View Results DataFrame and metadata."""
    return (
        st.session_state.view_results_model_id,
        st.session_state.view_results_dataframe,
        st.session_state.view_results_metadata
    )

def clear_view_results_cache():
    """Clear the View Results cache."""
    st.session_state.view_results_model_id = None
    st.session_state.view_results_dataframe = None
    st.session_state.view_results_metadata = {}

def display_results_dataframe(df: pd.DataFrame, model_id: str, total_count: int):
    """Display the results DataFrame with stats and download option."""
    st.success(f"📊 Found {total_count} results for model: {model_id}")
    
    # Display results
    st.subheader("Simulation Results")
    
    # Show basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Results", len(df))
    with col2:
        # Success rate based on absence of stderr
        if 'stderr' in df.columns:
            success_count = len(df[df['stderr'].isna() | (df['stderr'] == '')])
            success_rate = f"{success_count/len(df)*100:.1f}%"
        else:
            # If no stderr column, assume all succeeded
            success_rate = "100.0%"
        st.metric("Success Rate", success_rate)
    with col3:
        # Try to find an execution time column
        time_cols = [c for c in df.columns if c.lower().endswith("execution_time") or c.lower() == "execution_time"]
        avg_time = None
        for tc in time_cols:
            try:
                avg_time = pd.to_numeric(df[tc], errors='coerce').dropna().mean()
                break
            except Exception:
                continue
        st.metric("Avg Execution Time", f"{avg_time:.3f}s" if avg_time is not None else "N/A")
    
    # Show results table - handle complex data types
    try:
        # Create a display-safe version of the DataFrame
        display_df = make_display_safe(df)
        st.dataframe(display_df, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not display full DataFrame: {e}")
        # Show a simplified version
        st.write("**Available columns:**")
        st.write(list(df.columns))
        st.write("**First few rows (simplified):**")
        for i, row in df.head(3).iterrows():
            st.write(f"Row {i}:")
            for col in df.columns:
                try:
                    val = row[col]
                    if isinstance(val, (dict, list, tuple)):
                        st.write(f"  {col}: {type(val).__name__} (length: {len(val) if hasattr(val, '__len__') else 'N/A'})")
                    else:
                        st.write(f"  {col}: {val}")
                except Exception:
                    st.write(f"  {col}: <complex object>")
    
    # Download option - handle complex data types
    try:
        # Create a CSV-safe version of the DataFrame
        csv_df = make_display_safe(df)
        csv = csv_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"{model_id}_results.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.warning(f"Could not generate CSV download: {e}")
        st.info("CSV download unavailable due to complex data types in results.")

# ─────────────────────────────────────────────────────────────────────
# Streamlit Configuration
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SimExR - Simulation Explorer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────
# Session State Management
# ─────────────────────────────────────────────────────────────────────

# Initialize session state for caching
if "selected_model_id" not in st.session_state:
    st.session_state.selected_model_id = None
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

# Enhanced result caching per model
if "model_simulation_results" not in st.session_state:
    st.session_state.model_simulation_results = {}  # {model_id: {results, timestamp}}
if "last_simulation_model" not in st.session_state:
    st.session_state.last_simulation_model = None

# View Results page persistent state
if "view_results_model_id" not in st.session_state:
    st.session_state.view_results_model_id = None
if "view_results_dataframe" not in st.session_state:
    st.session_state.view_results_dataframe = None
if "view_results_metadata" not in st.session_state:
    st.session_state.view_results_metadata = {}

# Cache for model data and results
if "cached_model_info" not in st.session_state:
    st.session_state.cached_model_info = {}
if "cached_model_results" not in st.session_state:
    st.session_state.cached_model_results = {}
if "cached_model_code" not in st.session_state:
    st.session_state.cached_model_code = {}
if "cached_search_results" not in st.session_state:
    st.session_state.cached_search_results = {}

# Parameter annotations state
if "parameter_changes" not in st.session_state:
    st.session_state.parameter_changes = {}
if "original_parameters" not in st.session_state:
    st.session_state.original_parameters = {}
if "current_script" not in st.session_state:
    st.session_state.current_script = ""

# ─────────────────────────────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────────────────────────────

# Check API health
if not check_api_health():
    st.error("🚨 API server is not running! Please start the server with:")
    st.code("python start_api.py --host 127.0.0.1 --port 8000")
    st.stop()

# Sidebar
st.sidebar.title("🔬 SimExR")
st.sidebar.markdown("Simulation Execution & Reasoning Framework")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "📥 Import Models", "⚙️ Run Simulations", "📊 View Results", "🤖 AI Analysis", "📝 Parameter Annotations", "🔍 Model Search"]
)

# ─────────────────────────────────────────────────────────────────────
# Dashboard Page
# ─────────────────────────────────────────────────────────────────────

if page == "🏠 Dashboard":
    st.title("🏠 SimExR Dashboard")
    st.markdown("Welcome to the Simulation Execution & Reasoning Framework!")
    
    # Show cached results banner
    display_cached_results_banner()
    
    # System Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("API Status", "🟢 Online")
    
    with col2:
        st.metric("API Status", "🟢 Online")
    
    with col3:
        st.metric("Framework", "SimExR v1.0")
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Import New Model", use_container_width=True):
            st.info("Navigate to 'Import Models' in the sidebar")
    
    with col2:
        if st.button("🔍 Search Models", use_container_width=True):
            st.info("Navigate to 'Model Search' in the sidebar")
    
    with col3:
        if st.button("🤖 AI Analysis", use_container_width=True):
            st.info("Navigate to 'AI Analysis' in the sidebar")
    
    # Cache Management
    st.subheader("🗄️ Cache Management")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Cached Models", len(st.session_state.cached_model_info))
    
    with col2:
        st.metric("Cached Results", len(st.session_state.cached_model_results))
    
    with col3:
        st.metric("Cached Code", len(st.session_state.cached_model_code))
    
    with col4:
        st.metric("Search Cache", len(st.session_state.cached_search_results))
    
    # Cache controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            clear_model_cache()
            st.success("✅ Cache cleared! Data will be refreshed on next access.")
            st.rerun()
    
    with col2:
        if st.button("📊 Show Cache Details", use_container_width=True):
            with st.expander("Cache Details"):
                st.write("**Cached Models:**", list(st.session_state.cached_model_info.keys()))
                st.write("**Cached Results:**", list(st.session_state.cached_model_results.keys()))
                st.write("**Cached Code:**", list(st.session_state.cached_model_code.keys()))
                st.write("**Search Cache:**", list(st.session_state.cached_search_results.keys()))
    
    # Recent Activity
    st.subheader("📈 Recent Activity")
    
    # Get recent reasoning conversations
    conversations = make_api_request("GET", "/reasoning/conversations?limit=5")
    if "error" not in conversations and conversations.get("conversations"):
        for conv in conversations["conversations"][:3]:
            with st.expander(f"💬 {conv.get('question', 'Question')[:50]}..."):
                st.write(f"**Model:** {conv.get('model_id', 'Unknown')}")
                st.write(f"**Time:** {conv.get('timestamp', 'Unknown')}")
                st.write(f"**Answer:** {conv.get('answer', 'No answer')[:200]}...")
    else:
        st.info("No recent conversations found.")

# ─────────────────────────────────────────────────────────────────────
# Import Models Page
# ─────────────────────────────────────────────────────────────────────

elif page == "📥 Import Models":
    st.title("📥 Import Models")
    
    # Import from GitHub
    st.header("Import from GitHub")
    
    github_url = st.text_input(
        "GitHub URL",
        placeholder="https://github.com/user/repo/blob/main/script.py",
        help="Paste the GitHub URL of the script you want to import"
    )
    
    model_name = st.text_input(
        "Model Name",
        placeholder="my_custom_model",
        help="Give your model a descriptive name"
    )
    
    max_smoke_iters = st.slider(
        "Max Smoke Test Iterations",
        min_value=1,
        max_value=10,
        value=3,
        help="Number of iterations to test and fix the imported code"
    )
    
    if st.button("🚀 Import & Transform", type="primary"):
        if not github_url or not model_name:
            st.error("Please provide both GitHub URL and model name.")
        else:
            with st.spinner("Importing and transforming script..."):
                params = {
                    "github_url": github_url,
                    "model_name": model_name,
                    "max_smoke_iters": max_smoke_iters
                }
                
                result = make_api_request("POST", "/simulation/transform/github", params=params)
                
                if "error" not in result:
                    model_id = result.get('model_id')
                    st.success(f"✅ Successfully imported model: {model_id}")
                    
                    # Clear cache for new model to ensure fresh data
                    clear_model_cache(model_id)
                    
                    # Show model details
                    with st.expander("📋 Model Details"):
                        st.json(result)
                    
                    # Set as selected model
                    st.session_state.selected_model_id = model_id
                    st.info(f"Model '{model_name}' is now ready for simulation!")
                else:
                    st.error(f"❌ Import failed: {result.get('error')}")

# ─────────────────────────────────────────────────────────────────────
# Run Simulations Page
# ─────────────────────────────────────────────────────────────────────

elif page == "⚙️ Run Simulations":
    st.title("⚙️ Run Simulations")
    
    # Model Selection
    st.header("1. Select Model")
    
    # Search for models
    search_query = st.text_input("Search models", placeholder="Enter model name...")
    
    if search_query:
        models = search_models(search_query, limit=10)
        if models:
            model_options = {f"{m['name']} ({m['id']})": m['id'] for m in models}
            selected_model = st.selectbox("Choose a model", list(model_options.keys()))
            
            if selected_model:
                model_id = model_options[selected_model]
                st.session_state.selected_model_id = model_id
                
                # Show model info
                model_info = get_model_info(model_id)
                if model_info:
                    with st.expander("📋 Model Information"):
                        st.json(model_info)
        else:
            st.warning("No models found matching your search.")
    
    # Simulation Parameters
    if st.session_state.selected_model_id:
        st.header("2. Simulation Parameters")
        
        # Simple parameter input for now
        st.info("Enter simulation parameters as JSON:")
        
        params_json = st.text_area(
            "Parameters (JSON format)",
            value='{\n  "mu": 1.5,\n  "z0": [1.5, 0.5],\n  "eval_time": 25,\n  "t_iteration": 250,\n  "plot": false\n}',
            height=200
        )
        
        # Simulation Type
        sim_type = st.radio("Simulation Type", ["Single Run", "Batch Run"])
        
        if sim_type == "Single Run":
            if st.button("▶️ Run Single Simulation", type="primary"):
                try:
                    params = json.loads(params_json)
                    
                    with st.spinner("Running simulation..."):
                        data = {
                            "model_id": st.session_state.selected_model_id,
                            "parameters": params
                        }
                        
                        result = make_api_request("POST", "/simulation/run", data)
                        
                        if "error" not in result:
                            st.success("✅ Simulation completed successfully!")
                            
                            # Clear cache for this model to ensure fresh results
                            clear_model_cache(st.session_state.selected_model_id)
                            
                            # Store results with enhanced caching
                            store_simulation_results(st.session_state.selected_model_id, result, "single")
                            
                            # Show results
                            with st.expander("📊 Simulation Results"):
                                st.json(result)
                        else:
                            st.error(f"❌ Simulation failed: {result.get('error')}")
                            
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")
        
        else:  # Batch Run
            st.info("For batch runs, provide multiple parameter sets:")
            
            batch_params_json = st.text_area(
                "Batch Parameters (JSON array)",
                value='[\n  {\n    "mu": 1.0,\n    "z0": [2, 0],\n    "eval_time": 30,\n    "t_iteration": 300,\n    "plot": false\n  },\n  {\n    "mu": 1.5,\n    "z0": [1.5, 0.5],\n    "eval_time": 25,\n    "t_iteration": 250,\n    "plot": false\n  }\n]',
                height=200
            )
            
            if st.button("▶️ Run Batch Simulation", type="primary"):
                try:
                    param_grid = json.loads(batch_params_json)
                    
                    with st.spinner("Running batch simulation..."):
                        data = {
                            "model_id": st.session_state.selected_model_id,
                            "parameter_grid": param_grid
                        }
                        
                        result = make_api_request("POST", "/simulation/batch", data)
                        
                        if "error" not in result:
                            st.success(f"✅ Batch simulation completed! {len(result.get('results', []))} simulations run.")
                            
                            # Clear cache for this model to ensure fresh results
                            clear_model_cache(st.session_state.selected_model_id)
                            
                            # Store results with enhanced caching
                            store_simulation_results(st.session_state.selected_model_id, result, "batch")
                            
                            # Show results summary
                            with st.expander("📊 Batch Results Summary"):
                                st.json(result)
                        else:
                            st.error(f"❌ Batch simulation failed: {result.get('error')}")
                            
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")

# ─────────────────────────────────────────────────────────────────────
# View Results Page
# ─────────────────────────────────────────────────────────────────────

elif page == "📊 View Results":
    st.title("📊 View Results")
    
    # Show cached results banner
    display_cached_results_banner()
    
    # Get current cached state
    cached_model_id, cached_df, cached_metadata = get_cached_view_results()
    
    # Model Selection
    st.header("Select Model")
    
    search_query = st.text_input("Search models for results", placeholder="Enter model name...")
    
    # Show currently cached model info if available
    if cached_model_id:
        st.info(f"💾 **Currently Displaying**: Model `{cached_model_id}` ({len(cached_df) if cached_df is not None else 0} results)")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Refresh Current Model"):
                # Refresh the current model
                results = get_model_results(cached_model_id, limit=100)
                if results and results.get("results"):
                    try:
                        df = pd.json_normalize(results["results"], sep=".")
                    except Exception:
                        df = pd.DataFrame(results["results"])
                    
                    # Cache the new results
                    metadata = {
                        "total_count": results.get('total_count', 0),
                        "timestamp": time.time()
                    }
                    cache_view_results(cached_model_id, df, metadata)
                    st.success("✅ Results refreshed!")
                    st.rerun()
                else:
                    st.error("❌ No results found for current model")
        
        with col2:
            if st.button("🗑️ Clear Results"):
                clear_view_results_cache()
                st.success("✅ Results cleared!")
                st.rerun()
    
    if search_query:
        models = search_models(search_query, limit=10)
        if models:
            model_options = {f"{m['name']} ({m['id']})": m['id'] for m in models}
            selected_model = st.selectbox("Choose a model", list(model_options.keys()))
            
            if selected_model:
                model_id = model_options[selected_model]
                
                # Check if this is a different model than currently cached
                if model_id != cached_model_id:
                    if st.button(f"📊 Load Results for {model_id}", type="primary"):
                        with st.spinner("Loading results..."):
                            # Get results
                            results = get_model_results(model_id, limit=100)
                            
                            if results and results.get("results"):
                                # Convert to DataFrame and flatten all nested structures
                                try:
                                    df = pd.json_normalize(results["results"], sep=".")
                                except Exception:
                                    df = pd.DataFrame(results["results"])
                                
                                # Cache the results
                                metadata = {
                                    "total_count": results.get('total_count', 0),
                                    "timestamp": time.time()
                                }
                                cache_view_results(model_id, df, metadata)
                                
                                # Store for other pages
                                st.session_state.simulation_results = results
                                st.session_state.selected_model_id = model_id
                                
                                st.success(f"✅ Loaded {metadata['total_count']} results!")
                                st.rerun()
                            else:
                                st.warning("No results found for this model.")
                else:
                    st.info(f"ℹ️ Model `{model_id}` is already loaded. Results are displayed below.")
        else:
            st.warning("No models found matching your search.")
    
    # Display cached results if available
    if cached_df is not None and cached_model_id:
        st.markdown("---")
        display_results_dataframe(cached_df, cached_model_id, cached_metadata.get("total_count", len(cached_df)))
    elif not search_query:
        st.info("🔍 **Search for a model above to load its results**")
        st.markdown("Results will remain visible until you select a different model.")

# ─────────────────────────────────────────────────────────────────────
# AI Analysis Page
# ─────────────────────────────────────────────────────────────────────

elif page == "🤖 AI Analysis":
    st.title("🤖 AI Analysis")
    
    # Show cached results banner
    display_cached_results_banner()
    
    # Model Selection
    if not st.session_state.selected_model_id:
        st.header("1. Select Model")
        
        search_query = st.text_input("Search models for analysis", placeholder="Enter model name...")
        
        if search_query:
            models = search_models(search_query, limit=10)
            if models:
                model_options = {f"{m['name']} ({m['id']})": m['id'] for m in models}
                selected_model = st.selectbox("Choose a model", list(model_options.keys()))
                
                if selected_model:
                    st.session_state.selected_model_id = model_options[selected_model]
                    st.success(f"✅ Selected model: {selected_model}")
            else:
                st.warning("No models found matching your search.")
    
    # AI Analysis
    if st.session_state.selected_model_id:
        st.header("2. AI Chatbot")
        
        # Show selected model
        st.info(f"📋 Chatting about model: {st.session_state.selected_model_id}")
        
        # Chat settings at the top
        st.subheader("⚙️ Chat Settings")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            max_steps = st.number_input(
                "Max Reasoning Steps",
                min_value=1,
                max_value=20,
                value=5,
                help="Maximum reasoning steps for complex questions (1-20)"
            )
        
        with col2:
            st.markdown("💡 **Tip**: Higher step values allow for more complex reasoning but may take longer to respond.")
        
        # Initialize chat history for this model if not exists
        model_chat_key = f"chat_history_{st.session_state.selected_model_id}"
        if model_chat_key not in st.session_state:
            st.session_state[model_chat_key] = []
        
        # Display chat messages
        st.subheader("💬 Conversation")
        
        # Show welcome message if no chat history
        if not st.session_state[model_chat_key]:
            # Use Streamlit's built-in styling for better theme compatibility
            with st.container():
                st.markdown("### 🤖 Welcome to AI Analysis!")
                
                st.info("""
                **I'm your AI assistant for analyzing simulation results!** 
                
                I can help you understand your model's behavior, interpret results, and answer questions about your simulations.
                """)
                
                st.markdown("#### 💡 What you can ask me:")
                
                st.markdown("**🎯 System Stability & Parameter Analysis:**")
                st.markdown("- 🔍 Can you identify specific values or ranges of parameters corresponding to stable/unstable behavior of the system?")
                
                st.markdown("")  # Spacer
                st.markdown("**📊 Data Sufficiency & System Characteristics:**")
                st.markdown("- 📈 Can you explain if the data is sufficient to explain specific system characteristics?")
                st.markdown("- 🎯 Find a parameter value where the system will be stable (stays at single value) for a period of time")
                
                st.markdown("")  # Spacer
                st.markdown("**🔄 Periodic Behavior & Orbit Analysis:**")
                st.markdown("- 🌀 Find me a parameter range for which the system has a periodic orbit")
                st.markdown("- ⏱️ Analyze periodicity within specified time ranges")
                st.markdown("- 🔬 Identify specific dynamical system behaviors (equilibrium, limit cycles, chaos)")
                
                st.success("**Ready to help! Start by typing your question below! 👇**")
        
        # Display existing chat messages
        for i, chat in enumerate(st.session_state[model_chat_key]):
            if chat["role"] == "user":
                message(chat["content"], is_user=True, key=f"user_{i}")
            elif chat.get("is_thinking"):
                # Show thinking indicator
                with st.container():
                    st.markdown("🤔 **AI Assistant**: Thinking...")
                    st.progress(0)  # Show progress bar
            else:
                message(chat["content"], is_user=False, key=f"assistant_{i}")
                
                # Display images if they exist
                if chat.get("images"):
                    for img_path in chat["images"]:
                        try:
                            if Path(img_path).exists():
                                st.image(img_path, caption="Generated Plot", use_column_width=True)
                            else:
                                st.warning(f"Image not found: {img_path}")
                        except Exception as e:
                            st.error(f"Error displaying image {img_path}: {e}")
        
        # Chat input area
        st.markdown("---")
        st.markdown("### 💭 Ask a Question")
        
        # Create a form for the chat input
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_area(
                    "Type your message...",
                    placeholder="Ask me anything about your simulation results...",
                    height=60,
                    key="user_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
                submit_button = st.form_submit_button("🚀 Send", type="primary", use_container_width=True)
        
        # Handle chat submission
        if submit_button and user_input.strip():
            # Add user message to chat immediately
            st.session_state[model_chat_key].append({
                "role": "user",
                "content": user_input,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Add a temporary "thinking" message
            thinking_message = {
                "role": "assistant",
                "content": "🤔 Thinking...",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_thinking": True
            }
            st.session_state[model_chat_key].append(thinking_message)
            
            # Force rerun to show user message immediately
            st.rerun()
        
        # Check if we need to process a thinking message
        if st.session_state[model_chat_key] and st.session_state[model_chat_key][-1].get("is_thinking"):
            # Remove the thinking message
            st.session_state[model_chat_key].pop()
            
            # Get the last user message
            last_user_message = st.session_state[model_chat_key][-1]["content"]
            
            # Show loading indicator
            with st.spinner("🤖 AI is analyzing your question..."):
                result = ask_reasoning_question(
                    st.session_state.selected_model_id,
                    last_user_message,
                    max_steps
                )
                
                if "error" not in result:
                    ai_response = result.get("answer", "I apologize, but I couldn't generate a response for your question.")
                    images = result.get("images", [])
                    
                    # Add AI response to chat
                    st.session_state[model_chat_key].append({
                        "role": "assistant",
                        "content": ai_response,
                        "images": images,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    st.success("✅ Response generated!")
                    st.rerun()  # Refresh to show new messages
                else:
                    # Add error message to chat
                    st.session_state[model_chat_key].append({
                        "role": "assistant",
                        "content": f"❌ Sorry, I encountered an error: {result.get('error')}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.error(f"❌ AI analysis failed: {result.get('error')}")
                    st.rerun()
        
        # Chat controls
        st.subheader("⚙️ Chat Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Chat History"):
                st.session_state[model_chat_key] = []
                st.rerun()
        
        with col2:
            if st.session_state[model_chat_key]:
                # Create export data
                chat_text = "\n\n".join([
                    f"**{chat['role'].title()}** ({chat['timestamp']}):\n{chat['content']}"
                    for chat in st.session_state[model_chat_key]
                ])
                
                # Add metadata header
                export_content = f"""SimExR AI Chat Export
                Model: {st.session_state.selected_model_id}
                Export Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
                Total Messages: {len(st.session_state[model_chat_key])}

                {'='*50}

                {chat_text}
                """
                
                st.download_button(
                    label="📥 Export Chat",
                    data=export_content,
                    file_name=f"simexr_chat_{st.session_state.selected_model_id}_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    help="Download the complete chat history as a text file"
                )
            else:
                st.button("📥 Export Chat", disabled=True, help="No chat history to export")
        
        with col3:
            if st.button("🔄 New Conversation"):
                st.session_state[model_chat_key] = []
                st.rerun()

# ─────────────────────────────────────────────────────────────────────
# Parameter Annotations Page
# ─────────────────────────────────────────────────────────────────────

elif page == "📝 Parameter Annotations":
    st.title("📝 Parameter Annotations & Script Management")
    
    # Model Selection
    st.header("1. Select Model")
    
    search_query = st.text_input("Search models", placeholder="Enter model name...")
    
    if search_query:
        models = search_models(search_query, limit=10)
        if models:
            model_options = {f"{m['name']} ({m['id']})": m['id'] for m in models}
            selected_model = st.selectbox("Choose a model", list(model_options.keys()))
            
            if selected_model:
                model_id = model_options[selected_model]
                st.session_state.selected_model_id = model_id
                
                # Get model info
                model_info = get_model_info(model_id)
                
                if model_info:
                    st.success(f"✅ Selected model: {model_info.get('name', model_id)}")
                    
                    # Display model metadata
                    with st.expander("📋 Model Information"):
                        st.json(model_info)
                    
                    # Extract parameters from model info
                    extracted_params = model_info.get('parameters', {})
                    
                    if extracted_params:
                        st.header("2. Extracted Parameters")
                        
                        # Store original parameters if not already stored
                        if model_id not in st.session_state.original_parameters:
                            st.session_state.original_parameters[model_id] = extracted_params.copy()
                            st.session_state.parameter_changes[model_id] = {}
                        
                        # Display parameters with change tracking
                        st.subheader("📊 Parameter Visualization")
                        
                        # Create parameter editing interface
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("### 🔧 Edit Parameters")
                            
                            # Parameter editing form
                            with st.form("parameter_form"):
                                updated_params = {}
                                
                                for param_name, param_info in extracted_params.items():
                                    param_type = param_info.get('type', 'string')
                                    param_description = param_info.get('description', '')
                                    param_default = param_info.get('default', '')
                                    
                                    st.markdown(f"**{param_name}** ({param_type})")
                                    if param_description:
                                        st.caption(f"Description: {param_description}")
                                    
                                    # Create appropriate input based on type
                                    if param_type == 'number':
                                        value = st.number_input(
                                            f"Value for {param_name}",
                                            value=float(param_default) if param_default else 0.0,
                                            key=f"param_{model_id}_{param_name}"
                                        )
                                    elif param_type == 'boolean':
                                        value = st.checkbox(
                                            f"Value for {param_name}",
                                            value=bool(param_default) if param_default else False,
                                            key=f"param_{model_id}_{param_name}"
                                        )
                                    elif param_type == 'array':
                                        # For arrays, provide a text input that can be parsed as JSON
                                        value_str = st.text_input(
                                            f"Value for {param_name} (JSON array)",
                                            value=json.dumps(param_default) if param_default else "[]",
                                            key=f"param_{model_id}_{param_name}"
                                        )
                                        try:
                                            value = json.loads(value_str)
                                        except json.JSONDecodeError:
                                            value = param_default
                                    else:
                                        value = st.text_input(
                                            f"Value for {param_name}",
                                            value=str(param_default) if param_default else "",
                                            key=f"param_{model_id}_{param_name}"
                                        )
                                    
                                    updated_params[param_name] = value
                                    
                                    # Track changes
                                    original_value = st.session_state.original_parameters[model_id].get(param_name, {}).get('default', '')
                                    if value != original_value:
                                        st.session_state.parameter_changes[model_id][param_name] = {
                                            'original': original_value,
                                            'current': value,
                                            'changed': True
                                        }
                                    else:
                                        if param_name in st.session_state.parameter_changes[model_id]:
                                            del st.session_state.parameter_changes[model_id][param_name]
                                
                                submit_params = st.form_submit_button("💾 Save Parameter Changes")
                        
                        with col2:
                            st.markdown("### 📈 Change Tracking")
                            
                            # Show parameter changes
                            changes = st.session_state.parameter_changes.get(model_id, {})
                            
                            if changes:
                                st.success(f"🔄 {len(changes)} parameters modified")
                                
                                for param_name, change_info in changes.items():
                                    with st.expander(f"📝 {param_name}"):
                                        st.write(f"**Original:** {change_info['original']}")
                                        st.write(f"**Current:** {change_info['current']}")
                                        st.write(f"**Status:** Modified")
                            else:
                                st.info("✅ No parameter changes detected")
                            
                            # Quick actions
                            st.markdown("### ⚡ Quick Actions")
                            
                            if st.button("🔄 Reset All Parameters"):
                                st.session_state.parameter_changes[model_id] = {}
                                st.rerun()
                            
                            if st.button("📊 Export Parameters"):
                                param_data = {
                                    "model_id": model_id,
                                    "parameters": updated_params,
                                    "changes": changes
                                }
                                st.download_button(
                                    label="📄 Download Parameters",
                                    data=json.dumps(param_data, indent=2),
                                    file_name=f"{model_id}_parameters.json",
                                    mime="application/json"
                                )
                    
                    # Script Management
                    st.header("3. Script Management")
                    
                    # Get current script
                    script_result = make_api_request("GET", f"/simulation/models/{model_id}/script")
                    
                    if "error" not in script_result:
                        current_script = script_result.get("script", "")
                        is_placeholder = script_result.get("is_placeholder", False)
                        
                        if is_placeholder:
                            st.subheader("📝 Script Editor (Placeholder)")
                            st.warning("⚠️ This model doesn't have a script file yet. You can create one by editing the placeholder below.")
                        else:
                            st.subheader("📝 Refactored Script")
                        
                        # Script editing
                        edited_script = st.text_area(
                            "Edit the script:",
                            value=current_script,
                            height=400,
                            key=f"script_{model_id}"
                        )
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 Save Script Changes"):
                                result = save_model_script(model_id, edited_script)
                                if "error" not in result:
                                    st.success("✅ Script saved successfully!")
                                else:
                                    st.error(f"❌ Failed to save script: {result.get('error')}")
                        
                        with col2:
                            if st.button("🔄 Reset Script"):
                                st.rerun()
                        
                        # Script preview
                        with st.expander("👀 Script Preview"):
                            st.code(edited_script, language="python")
                    
                    # Simulation with updated parameters
                    st.header("4. Quick Simulation")
                    
                    if st.button("🚀 Run Simulation with Current Parameters"):
                        # Get the updated parameters from the form
                        updated_params = {}
                        for param_name in extracted_params.keys():
                            param_key = f"param_{model_id}_{param_name}"
                            if param_key in st.session_state:
                                updated_params[param_name] = st.session_state[param_key]
                        
                        if updated_params:
                            with st.spinner("Running simulation with updated parameters..."):
                                data = {
                                    "model_id": model_id,
                                    "parameters": updated_params
                                }
                                
                                result = make_api_request("POST", "/simulation/run", data)
                                
                                if "error" not in result:
                                    st.success("✅ Simulation completed successfully!")
                                    
                                    # Store results with enhanced caching
                                    store_simulation_results(model_id, result, "single")
                                    
                                    with st.expander("📊 Simulation Results"):
                                        st.json(result)
                                else:
                                    st.error(f"❌ Simulation failed: {result.get('error')}")
                        else:
                            st.warning("⚠️ No parameters available for simulation")
                    
                else:
                    st.error("❌ Failed to load model information")
            else:
                st.info("Please select a model to continue")
        else:
            st.warning("No models found matching your search.")
    else:
        st.info("🔍 Enter a model name to search and get started with parameter annotations")

# ─────────────────────────────────────────────────────────────────────
# Model Search Page
# ─────────────────────────────────────────────────────────────────────

elif page == "🔍 Model Search":
    st.title("🔍 Model Search")
    
    # Search interface
    search_query = st.text_input(
        "Search models by name",
        placeholder="e.g., vanderpol, lorenz, pendulum...",
        help="Enter part of a model name to search"
    )
    
    limit = st.slider("Max results", 5, 50, 20)
    
    if search_query:
        with st.spinner("Searching models..."):
            models = search_models(search_query, limit)
        
        if models:
            st.success(f"🔍 Found {len(models)} models")
            
            # Display models
            for i, model in enumerate(models):
                with st.expander(f"📋 {model.get('name', 'Unknown')} ({model.get('id', 'No ID')})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**ID:** {model.get('id', 'N/A')}")
                        st.write(f"**Name:** {model.get('name', 'N/A')}")
                        st.write(f"**Script Path:** {model.get('script_path', 'N/A')}")
                        
                        # Show metadata if available
                        if model.get('metadata'):
                            try:
                                metadata = json.loads(model['metadata']) if isinstance(model['metadata'], str) else model['metadata']
                                st.write("**Metadata:**")
                                st.json(metadata)
                            except:
                                st.write(f"**Metadata:** {model['metadata']}")
                    
                    with col2:
                        if st.button(f"Select Model {i+1}", key=f"select_{i}"):
                            st.session_state.selected_model_id = model.get('id')
                            st.success(f"✅ Selected: {model.get('name')}")
                        
                        if st.button(f"View Results {i+1}", key=f"results_{i}"):
                            st.session_state.selected_model_id = model.get('id')
                            st.info("Navigate to 'View Results' in the sidebar to see the results")
        else:
            st.warning("No models found matching your search.")
    
    # Show all models
    else:
        st.subheader("All Available Models")
        
        # Get all models
        all_models = make_api_request("GET", "/simulation/models")
        
        if "error" not in all_models and all_models.get("models"):
            models = all_models["models"]
            st.info(f"📊 Total models: {len(models)}")
            
            # Display in a table
            model_data = []
            for model in models[:50]:  # Limit to first 50
                model_data.append({
                    "Name": model.get('name', 'N/A'),
                    "ID": model.get('id', 'N/A')[:20] + "..." if len(model.get('id', '')) > 20 else model.get('id', 'N/A'),
                    "Script Path": model.get('script_path', 'N/A')
                })
            
            df = pd.DataFrame(model_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to load models.")

# ─────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.markdown("**API Status:** 🟢 Online")
st.sidebar.markdown(f"**Server:** {API_BASE_URL}")

# Debug info
if st.sidebar.checkbox("Show Debug Info"):
    # Count total chat messages across all models
    total_chat_messages = 0
    for key in st.session_state.keys():
        if key.startswith("chat_history_"):
            total_chat_messages += len(st.session_state[key])
    
    st.sidebar.json({
        "selected_model": st.session_state.selected_model_id,
        "total_chat_messages": total_chat_messages,
        "has_results": st.session_state.simulation_results is not None,
        "cached_models": len(st.session_state.cached_model_info),
        "cached_results": len(st.session_state.cached_model_results),
        "cached_simulations": len(st.session_state.model_simulation_results),
        "last_simulation_model": st.session_state.last_simulation_model
    })
