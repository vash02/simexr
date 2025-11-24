def simulate(**params):
    import math
    results = {}
    try:
        import numpy as np
    except Exception as e:
        return {"success": False, "error": f"numpy import failed: {e}"}
    try:
        from scipy.integrate import solve_ivp
    except Exception as e:
        return {"success": False, "error": f"scipy.integrate.solve_ivp import failed: {e}"}

    # Default parameters
    defaults = {
        "alpha": 1.0,
        "beta": 0.1,
        "delta": 0.075,
        "gamma": 1.5,
        "t_span": (0.0, 60.0),
        "num_t": 2000,
        "t_eval": None,
        "x0": 10.0,
        "y0": 5.0,
        "method": "RK45",
        "rtol": 1e-8,
        "atol": 1e-10,
        "nx": 20,
        "ny": 20,
    }

    # Helper to coerce numeric types robustly
    def _to_float(v, default=0.0):
        try:
            if v is None:
                return float(default)
            if isinstance(v, (float, int, np.floating, np.integer)):
                return float(v)
            return float(str(v))
        except Exception:
            try:
                return float(default)
            except Exception:
                return 0.0

    def _to_int(v, default=0):
        try:
            if v is None:
                return int(default)
            if isinstance(v, (int, np.integer)):
                return int(v)
            return int(float(v))
        except Exception:
            try:
                return int(default)
            except Exception:
                return 0

    # Override defaults with params if provided
    for k in list(defaults.keys()):
        if k in params:
            defaults[k] = params[k]

    # Coerce scalar params
    alpha = _to_float(defaults["alpha"], 1.0)
    beta = _to_float(defaults["beta"], 0.1)
    delta = _to_float(defaults["delta"], 0.075)
    gamma = _to_float(defaults["gamma"], 1.5)
    x0 = _to_float(defaults["x0"], 10.0)
    y0 = _to_float(defaults["y0"], 5.0)
    method = defaults.get("method", "RK45")
    try:
        method = str(method)
    except Exception:
        method = "RK45"
    rtol = _to_float(defaults.get("rtol", 1e-8), 1e-8)
    atol = _to_float(defaults.get("atol", 1e-10), 1e-10)
    nx = _to_int(defaults.get("nx", 20), 20)
    ny = _to_int(defaults.get("ny", 20), 20)

    # Coerce t_span
    t_span_param = defaults.get("t_span", (0.0, 60.0))
    try:
        if isinstance(t_span_param, (list, tuple, np.ndarray)) and len(t_span_param) >= 2:
            t0 = _to_float(t_span_param[0], 0.0)
            t1 = _to_float(t_span_param[1], 60.0)
        else:
            # If single number given, treat as end time
            t0 = 0.0
            t1 = _to_float(t_span_param, 60.0)
        if not math.isfinite(t0):
            t0 = 0.0
        if not math.isfinite(t1) or t1 == t0:
            t1 = t0 + 60.0
        # Ensure t0 < t1
        if t1 < t0:
            t0, t1 = t1, t0
    except Exception:
        t0, t1 = 0.0, 60.0
    t_span = (float(t0), float(t1))

    # Coerce/construct t_eval
    t_eval_param = defaults.get("t_eval", None)
    num_t = _to_int(defaults.get("num_t", 2000), 2000)
    if t_eval_param is None:
        try:
            if num_t < 2:
                num_t = 2
            t_eval = np.linspace(t_span[0], t_span[1], num_t)
        except Exception:
            t_eval = np.linspace(0.0, 60.0, 2000)
    else:
        try:
            # Accept lists, tuples, numpy arrays, or comma-separated string
            if isinstance(t_eval_param, str):
                parts = [p.strip() for p in t_eval_param.split(",") if p.strip() != ""]
                t_eval = np.array([_to_float(p) for p in parts], dtype=float)
            else:
                t_eval = np.array(t_eval_param, dtype=float)
            # Filter/clip to t_span
            if t_eval.size == 0:
                t_eval = np.linspace(t_span[0], t_span[1], max(2, num_t))
            else:
                t_eval = t_eval[(t_eval >= t_span[0]) & (t_eval <= t_span[1])]
                if t_eval.size == 0:
                    t_eval = np.linspace(t_span[0], t_span[1], max(2, num_t))
        except Exception:
            t_eval = np.linspace(t_span[0], t_span[1], max(2, num_t))

    # Ensure initial conditions are finite
    if not math.isfinite(x0):
        x0 = 10.0
    if not math.isfinite(y0):
        y0 = 5.0

    # Prepare model function inline (lambda)
    # dx/dt = alpha * x - beta * x * y
    # dy/dt = delta * x * y - gamma * y
    def _wrapped_solve():
        try:
            sol = solve_ivp(
                fun=lambda t, z: [alpha * z[0] - beta * z[0] * z[1], delta * z[0] * z[1] - gamma * z[1]],
                t_span=t_span,
                y0=[x0, y0],
                method=method,
                t_eval=t_eval,
                rtol=rtol,
                atol=atol,
            )
            return sol
        except Exception as e:
            return e

    sol = _wrapped_solve()
    if isinstance(sol, Exception):
        return {"success": False, "error": f"Integration raised an exception: {sol}"}
    if not getattr(sol, "success", False):
        return {"success": False, "error": f"Integration failed: {getattr(sol, 'message', 'unknown')}"}

    # Extract solutions and convert to pure Python types
    try:
        t_out = [float(x) for x in np.array(sol.t, dtype=float).tolist()]
    except Exception:
        t_out = list(map(float, np.array(sol.t).astype(float).tolist()))
    try:
        y_all = np.array(sol.y)
        if y_all.shape[0] >= 2:
            x_arr = np.array(y_all[0], dtype=float)
            y_arr = np.array(y_all[1], dtype=float)
        else:
            # Unexpected shape: attempt to coerce
            flat = np.ravel(y_all)
            if flat.size >= 2:
                x_arr = np.array(flat[0::2], dtype=float)
                y_arr = np.array(flat[1::2], dtype=float)
                # Pad to t length if needed
                if x_arr.size < len(t_out):
                    x_arr = np.resize(x_arr, len(t_out))
                if y_arr.size < len(t_out):
                    y_arr = np.resize(y_arr, len(t_out))
            else:
                x_arr = np.zeros(len(t_out), dtype=float)
                y_arr = np.zeros(len(t_out), dtype=float)
    except Exception:
        # Fallback zeros
        x_arr = np.zeros(len(t_out), dtype=float)
        y_arr = np.zeros(len(t_out), dtype=float)

    x_list = [float(val) if (np.isfinite(val) or isinstance(val, (float, int))) else float("nan") for val in x_arr.tolist()]
    y_list = [float(val) if (np.isfinite(val) or isinstance(val, (float, int))) else float("nan") for val in y_arr.tolist()]

    # Equilibrium points with safe division
    def _safe_div(a, b):
        try:
            a_f = float(a)
            b_f = float(b)
            if b_f == 0:
                return None
            if not math.isfinite(a_f) or not math.isfinite(b_f):
                return None
            return a_f / b_f
        except Exception:
            return None

    e0 = (0.0, 0.0)
    e1_x = _safe_div(gamma, delta)
    e1_y = _safe_div(alpha, beta)
    e1 = (e1_x, e1_y)

    # Jacobian matrices at equilibria
    # J = [[alpha - beta*y, -beta*x],
    #      [delta*y,         delta*x - gamma]]
    def _jacobian(xv, yv):
        try:
            xv_f = _to_float(xv, 0.0)
            yv_f = _to_float(yv, 0.0)
            a = float(alpha) - float(beta) * yv_f
            b = -float(beta) * xv_f
            c = float(delta) * yv_f
            d = float(delta) * xv_f - float(gamma)
            return [[float(a), float(b)], [float(c), float(d)]]
        except Exception:
            return [[float("nan"), float("nan")], [float("nan"), float("nan")]]

    J_e0 = _jacobian(e0[0], e0[1])
    J_e1 = None
    if e1_x is None or e1_y is None:
        J_e1 = [[None, None], [None, None]]
    else:
        J_e1 = _jacobian(e1[0], e1[1])

    # Eigenvalues (use numpy, convert to Python complex/floats)
    eig_e0 = []
    eig_e1 = []
    try:
        J0_np = np.array(J_e0, dtype=float)
        vals0 = np.linalg.eigvals(J0_np)
        eig_e0 = [complex(v) for v in vals0.tolist()]
    except Exception:
        eig_e0 = []
    try:
        if e1_x is None or e1_y is None:
            eig_e1 = []
        else:
            J1_np = np.array(J_e1, dtype=float)
            vals1 = np.linalg.eigvals(J1_np)
            eig_e1 = [complex(v) for v in vals1.tolist()]
    except Exception:
        eig_e1 = []

    # Nullclines (safe)
    y_nc = _safe_div(alpha, beta)
    x_nc = _safe_div(gamma, delta)

    # Estimate oscillation periods from peaks of prey using scipy.signal.find_peaks if available
    periods = None
    peaks_idx = None
    try:
        from scipy.signal import find_peaks
        # convert x_arr to 1D numpy
        x_for_peaks = np.array(x_arr, dtype=float)
        if x_for_peaks.size > 3:
            # minimum distance in samples: try to enforce at least 1% of t samples
            min_dist = max(1, int(0.01 * max(1, len(t_out))))
            peaks_idx, _ = find_peaks(x_for_peaks, distance=min_dist)
            if peaks_idx is not None and len(peaks_idx) > 1:
                peak_times = np.array(t_out, dtype=float)[peaks_idx]
                periods_arr = np.diff(peak_times)
                # Filter non-finite values
                periods_arr = periods_arr[np.isfinite(periods_arr)]
                periods = [float(p) for p in periods_arr.tolist()] if periods_arr.size > 0 else []
            else:
                periods = []
        else:
            periods = []
    except Exception:
        periods = None
        peaks_idx = None

    # Assemble params_used (only simple builtins)
    params_used = {
        "alpha": float(alpha),
        "beta": float(beta),
        "delta": float(delta),
        "gamma": float(gamma),
        "t_span": (float(t_span[0]), float(t_span[1])),
        "method": str(method),
        "rtol": float(rtol),
        "atol": float(atol),
        "x0": float(x0),
        "y0": float(y0),
        "nx": int(nx),
        "ny": int(ny),
        "t_eval_length": int(len(t_eval)) if hasattr(t_eval, "__len__") else None,
    }

    # Convert Jacobians to builtins with None for NaN
    def _normalize_matrix(mat):
        out = []
        for row in mat:
            out_row = []
            for val in row:
                try:
                    if val is None:
                        out_row.append(None)
                    else:
                        v = float(val)
                        if not math.isfinite(v):
                            out_row.append(None)
                        else:
                            out_row.append(v)
                except Exception:
                    out_row.append(None)
            out.append(out_row)
        return out

    J_e0_out = _normalize_matrix(J_e0)
    J_e1_out = _normalize_matrix(J_e1) if J_e1 is not None else [[None, None], [None, None]]

    # Ensure outputs are basic python types
    results = {
        "success": True,
        "t": [float(v) for v in t_out],
        "x": [float(v) if (v is not None and (isinstance(v, (int, float)) or (isinstance(v, complex) and v.imag == 0))) else (float(v) if isinstance(v, (int, float)) else float("nan")) for v in x_list],
        "y": [float(v) if (v is not None and (isinstance(v, (int, float)) or (isinstance(v, complex) and v.imag == 0))) else (float(v) if isinstance(v, (int, float)) else float("nan")) for v in y_list],
        "equilibria": {"E0": (float(e0[0]), float(e0[1])), "E1": (None if e1[0] is None else float(e1[0]), None if e1[1] is None else float(e1[1]))},
        "jacobian": {"J_e0": J_e0_out, "J_e1": J_e1_out},
        "eigenvalues": {"eig_e0": eig_e0, "eig_e1": eig_e1},
        "nullclines": {"y_nc": (None if y_nc is None else float(y_nc)), "x_nc": (None if x_nc is None else float(x_nc))},
        "periods": (None if periods is None else [float(p) for p in periods]),
        "peaks_indices": (None if peaks_idx is None else [int(i) for i in peaks_idx.tolist()]),
        "params_used": params_used,
    }

    return results