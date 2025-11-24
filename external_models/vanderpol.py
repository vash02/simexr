def simulate(**params):
    import math
    try:
        import numpy as np
        from scipy.integrate import solve_ivp
        import matplotlib.pyplot as plt
    except Exception as e:
        return {"error": "Required libraries not available", "exception": str(e)}

    # small safe converters (lambdas to avoid top-level def)
    to_float = lambda v, default=0.0: default if v is None else (float(v) if not isinstance(v, (list, tuple)) else default)
    to_int = lambda v, default=0: default if v is None else (int(v) if not isinstance(v, (list, tuple)) else default)
    to_bool = lambda v, default=False: bool(v) if v is not None else default
    to_list_of_floats = lambda v, length=None, default=None: (
        list(map(float, v)) if v is not None and hasattr(v, '__iter__') else
        (default if default is not None else [])
    )

    # Default parameters (internal constants)
    defaults = {
        "eval_time": 100.0,
        "t_iteration": 1000,
        "z0": [2.0, 0.0],
        "mu": 1.0,
        "mgrid_size": 8.0,
        "grid_points": 15,
        "x_null_step": 0.001,
        "plot": False,
        "density": 2.0,
        "colormap": "cool",
        "streamplot_markersize": 2,
        "trajectory_lw": 3,
        "start_marker_size": 7,
        "end_marker_size": 7,
    }

    # Merge params with defaults, with type checking and conversion
    used = {}
    for k, v in defaults.items():
        if k in params:
            used[k] = params[k]
        else:
            used[k] = v

    # Ensure numeric types are correct
    try:
        eval_time = float(used.get("eval_time", defaults["eval_time"]))
    except Exception:
        eval_time = float(defaults["eval_time"])
    try:
        t_iteration = int(used.get("t_iteration", defaults["t_iteration"]))
        if t_iteration <= 1:
            t_iteration = int(defaults["t_iteration"])
    except Exception:
        t_iteration = int(defaults["t_iteration"])
    # t_span can be provided directly
    t_span_in = params.get("t_span", None)
    if t_span_in is None:
        t_span = [0.0, eval_time]
    else:
        try:
            # attempt to coerce to 2 floats
            if hasattr(t_span_in, "__iter__"):
                t_span = [float(t_span_in[0]), float(t_span_in[1])]
            else:
                t_span = [0.0, float(t_span_in)]
        except Exception:
            t_span = [0.0, eval_time]

    # t_eval may be provided; if not, generate
    t_eval_in = params.get("t_eval", None)
    try:
        if t_eval_in is None:
            t_eval = np.linspace(t_span[0], t_span[1], t_iteration)
        else:
            if hasattr(t_eval_in, "__iter__"):
                t_eval = np.array(list(map(float, t_eval_in)))
            else:
                # single number interpreted as iteration count
                t_eval = np.linspace(t_span[0], t_span[1], int(t_eval_in))
    except Exception:
        t_eval = np.linspace(t_span[0], t_span[1], t_iteration)

    # initial condition z0
    z0_in = params.get("z0", used["z0"])
    try:
        if z0_in is None:
            z0 = [float(defaults["z0"][0]), float(defaults["z0"][1])]
        elif hasattr(z0_in, "__iter__"):
            zlist = list(z0_in)
            if len(zlist) >= 2:
                z0 = [float(zlist[0]), float(zlist[1])]
            elif len(zlist) == 1:
                z0 = [float(zlist[0]), 0.0]
            else:
                z0 = [float(defaults["z0"][0]), float(defaults["z0"][1])]
        else:
            # single numeric value
            z0 = [float(z0_in), 0.0]
    except Exception:
        z0 = [float(defaults["z0"][0]), float(defaults["z0"][1])]

    # mu
    try:
        mu = float(params.get("mu", used["mu"]))
    except Exception:
        mu = float(defaults["mu"])

    # grid parameters
    try:
        mgrid_size = float(params.get("mgrid_size", used["mgrid_size"]))
        if mgrid_size <= 0:
            mgrid_size = float(defaults["mgrid_size"])
    except Exception:
        mgrid_size = float(defaults["mgrid_size"])
    try:
        grid_points = int(params.get("grid_points", used["grid_points"]))
        if grid_points < 2:
            grid_points = int(defaults["grid_points"])
    except Exception:
        grid_points = int(defaults["grid_points"])
    try:
        x_null_step = float(params.get("x_null_step", used["x_null_step"]))
        if x_null_step <= 0:
            x_null_step = float(defaults["x_null_step"])
    except Exception:
        x_null_step = float(defaults["x_null_step"])

    plot_flag = bool(params.get("plot", used["plot"]))
    density = float(params.get("density", used["density"]))
    cmap = params.get("colormap", used["colormap"])
    streamplot_markersize = float(params.get("streamplot_markersize", used["streamplot_markersize"]))
    trajectory_lw = float(params.get("trajectory_lw", used["trajectory_lw"]))
    start_marker_size = float(params.get("start_marker_size", used["start_marker_size"]))
    end_marker_size = float(params.get("end_marker_size", used["end_marker_size"]))

    # Build vector field arrays
    try:
        x_vals = np.linspace(-mgrid_size, mgrid_size, grid_points)
        y_vals = np.linspace(-mgrid_size, mgrid_size, grid_points)
        x_grid, y_grid = np.meshgrid(x_vals, y_vals)
        # vector field u = y, v = mu*(1-x^2)*y - x
        u_grid = np.array(y_grid, dtype=float)
        v_grid = mu * (1.0 - np.array(x_grid, dtype=float)**2) * np.array(y_grid, dtype=float) - np.array(x_grid, dtype=float)
    except Exception as e:
        return {"error": "Failed to build vector field", "exception": str(e)}

    # Solve the Van der Pol system using a lambda (no extra def)
    try:
        fun = lambda t, z: [z[1], mu * (1.0 - z[0]**2) * z[1] - z[0]]
        sol = solve_ivp(fun, t_span, z0, t_eval=t_eval, method=params.get("method", "RK45"))
        sol_t = sol.t
        sol_y = sol.y  # 2 x N
    except Exception as e:
        return {"error": "Integration failed", "exception": str(e)}

    # Nullclines
    try:
        x_null = np.arange(-mgrid_size, mgrid_size + x_null_step, x_null_step)
        denom = mu * (1.0 - x_null**2)
        # Avoid division by zero - set to nan where denom ~ 0
        with np.errstate(divide='ignore', invalid='ignore'):
            y_null = np.where(np.abs(denom) > 1e-12, x_null / denom, np.nan)
        x_nullcline = np.zeros_like(x_null)
    except Exception as e:
        return {"error": "Nullcline computation failed", "exception": str(e)}

    # Prepare results as built-in types only
    try:
        result = {
            "t": list(map(float, sol_t.tolist())),
            "x": list(map(float, sol_y[0].tolist())),
            "y": list(map(float, sol_y[1].tolist())),
            "vector_field": {
                "x_grid": x_grid.tolist(),
                "y_grid": y_grid.tolist(),
                "u_grid": u_grid.tolist(),
                "v_grid": v_grid.tolist()
            },
            "nullcline": {
                "x_null": list(map(float, x_null.tolist())),
                "y_null": [ (float(v) if (v is not None and (not (isinstance(v, float) and math.isnan(v)))) else None) for v in y_null.tolist() ],
                "x_nullcline": list(map(float, x_nullcline.tolist()))
            },
            "t_span": [float(t_span[0]), float(t_span[1])],
            "t_eval_length": int(len(t_eval)),
            "z0": [float(z0[0]), float(z0[1])],
            "mu": float(mu),
            "mgrid_size": float(mgrid_size),
            "grid_points": int(grid_points),
            "params_used": {k: params.get(k, defaults.get(k)) for k in set(list(defaults.keys()) + list(params.keys())) if k is not None}
        }
    except Exception as e:
        return {"error": "Result packaging failed", "exception": str(e)}

    # Optional plotting (not required; controlled by 'plot' param)
    if plot_flag:
        try:
            plt.figure(figsize=(6, 6))
            plt.clf()
            speed = np.sqrt(np.array(u_grid)**2 + np.array(v_grid)**2)
            # streamplot expects arrays; use the computed ones
            plt.streamplot(x_grid, y_grid, u_grid, v_grid, color=speed, cmap=cmap, density=density)
            # Plot nullclines: skip None entries
            x_null_plot = [float(x) for x, yv in zip(x_null.tolist(), y_null.tolist()) if not (isinstance(yv, float) and math.isnan(yv))]
            y_null_plot = [float(yv) for yv in y_null.tolist() if not (isinstance(yv, float) and math.isnan(yv))]
            if len(x_null_plot) > 0 and len(y_null_plot) > 0:
                plt.plot(x_null_plot, y_null_plot, '.', c="darkturquoise", markersize=streamplot_markersize)
            plt.plot(x_null.tolist(), [0.0]*len(x_null.tolist()), '.', c="darkturquoise", markersize=streamplot_markersize)
            plt.plot(result["x"], result["y"], 'r-', lw=trajectory_lw,
                     label=f'Trajectory for mu={mu} and z0={z0}')
            plt.plot(result["x"][0], result["y"][0], 'bo', label='start point', alpha=0.75, markersize=start_marker_size)
            plt.plot(result["x"][-1], result["y"][-1], 'o', c="yellow", label='end point', alpha=0.75, markersize=end_marker_size)
            plt.title('phase plane plot: Van der Pol oscillator')
            plt.xlabel('x')
            plt.ylabel('y')
            plt.legend(loc='lower right')
            ax = plt.gca()
            for spine in ['top', 'right', 'bottom', 'left']:
                try:
                    ax.spines[spine].set_visible(False)
                except Exception:
                    pass
            plt.ylim(-mgrid_size, mgrid_size)
            plt.tight_layout()
            plt.show()
            result["plot_shown"] = True
        except Exception as e:
            # don't fail the whole run because plotting failed; include warning
            result["plot_shown"] = False
            result["plot_exception"] = str(e)

    return result