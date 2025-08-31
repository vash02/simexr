def simulate(**params):
    try:
        import numpy as np
    except Exception as e:
        return {"error": "numpy import failed", "exception": str(e)}
    try:
        from scipy.integrate import solve_ivp
    except Exception as e:
        return {"error": "scipy.integrate.solve_ivp import failed", "exception": str(e)}
    messages = []
    # Helper to coerce numeric types safely
    def _to_float(v, default=0.0):
        try:
            if v is None:
                return float(default)
            if isinstance(v, (list, tuple, np.ndarray)):
                return float(v[0])
            return float(v)
        except Exception:
            try:
                return float(default)
            except Exception:
                return 0.0
    def _to_int(v, default=1):
        try:
            if v is None:
                return int(default)
            if isinstance(v, (list, tuple, np.ndarray)):
                return int(v[0])
            return int(v)
        except Exception:
            try:
                return int(default)
            except Exception:
                return 1
    # Override defaults with params (if present)
    eval_time = _to_float(params.get("eval_time", params.get("t_final", 100.0)), 100.0)
    t_iteration = _to_int(params.get("t_iteration", 1000), 1000)
    if t_iteration < 2:
        messages.append("t_iteration too small; setting to 2")
        t_iteration = 2
    # initial condition z0 should be a length-2 sequence
    z0_param = params.get("z0", [2, 0])
    try:
        if isinstance(z0_param, (list, tuple, np.ndarray)) and len(z0_param) >= 2:
            z0 = [float(z0_param[0]), float(z0_param[1])]
        else:
            # try to interpret single number as x0 with y0=0
            z0 = [float(z0_param), 0.0]
    except Exception:
        z0 = [2.0, 0.0]
        messages.append("z0 could not be parsed; using default [2,0]")
    mu = _to_float(params.get("mu", 1.0), 1.0)
    mgrid_size = _to_float(params.get("mgrid_size", 8.0), 8.0)
    grid_points = _to_int(params.get("gridpoints", params.get("mgridsize", 15)), 15)
    if grid_points < 2:
        messages.append("gridpoints too small; setting to 15")
        grid_points = 15
    # time span handling
    t_span_param = params.get("t_span", None)
    if t_span_param is None:
        t_span = [0.0, float(eval_time)]
    else:
        try:
            if isinstance(t_span_param, (list, tuple, np.ndarray)) and len(t_span_param) >= 2:
                t_span = [float(t_span_param[0]), float(t_span_param[1])]
            else:
                # single value interpreted as end time
                t_span = [0.0, float(t_span_param)]
        except Exception:
            t_span = [0.0, float(eval_time)]
            messages.append("t_span could not be parsed; using [0, eval_time]")
    # ensure t_span[1] > t_span[0]
    if t_span[1] <= t_span[0]:
        messages.append("t_span invalid (end <= start); adjusting to [0, eval_time]")
        t_span = [0.0, float(eval_time)]
    # t_eval handling
    t_eval_param = params.get("t_eval", None)
    if t_eval_param is None:
        try:
            t_eval = np.linspace(t_span[0], t_span[1], t_iteration)
        except Exception:
            t_eval = np.linspace(0.0, float(eval_time), max(2, t_iteration))
    else:
        try:
            t_eval_arr = np.array(t_eval_param, dtype=float)
            if t_eval_arr.ndim != 1 or t_eval_arr.size < 2:
                # fallback to linspace
                t_eval = np.linspace(t_span[0], t_span[1], t_iteration)
            else:
                t_eval = t_eval_arr
        except Exception:
            messages.append("t_eval could not be parsed; using linspace")
            t_eval = np.linspace(t_span[0], t_span[1], t_iteration)
    # ensure types
    try:
        eval_time = float(eval_time)
    except Exception:
        eval_time = 100.0
    try:
        mu = float(mu)
    except Exception:
        mu = 1.0
    try:
        mgrid_size = float(mgrid_size)
    except Exception:
        mgrid_size = 8.0
    # Build grid for vector field
    try:
        x_vals = np.linspace(-mgrid_size, mgrid_size, grid_points)
        y_vals = np.linspace(-mgrid_size, mgrid_size, grid_points)
        x_grid, y_grid = np.meshgrid(x_vals, y_vals)
        u_grid = y_grid
        v_grid = mu * (1 - x_grid**2) * y_grid - x_grid
    except Exception as e:
        return {"error": "failed to create vector field grid", "exception": str(e)}
    # Define van der Pol right-hand side as a lambda (no extra def)
    van_der_pol = lambda t, z, mu_local=mu: [z[1], mu_local * (1 - (z[0] ** 2)) * z[1] - z[0]]
    # Solve ODE
    solution = None
    sol_success = False
    sol_message = ""
    try:
        # solve_ivp tolerances may be optionally provided in params
        solver_kwargs = {}
        # allow passing atol and rtol as params if present
        if "atol" in params:
            try:
                solver_kwargs["atol"] = float(params["atol"])
            except Exception:
                messages.append("atol could not be parsed; ignored")
        if "rtol" in params:
            try:
                solver_kwargs["rtol"] = float(params["rtol"])
            except Exception:
                messages.append("rtol could not be parsed; ignored")
        solution = solve_ivp(lambda t, z: van_der_pol(t, z), t_span, [float(z0[0]), float(z0[1])],
                             t_eval=np.array(t_eval, dtype=float), **solver_kwargs)
        sol_success = bool(getattr(solution, "success", False))
        sol_message = str(getattr(solution, "message", ""))
    except Exception as e:
        sol_success = False
        sol_message = f"ODE solver failed: {e}"
        messages.append(sol_message)
    # Nullclines: x-nullcline is y=0; y-nullcline is x/(mu*(1-x^2))
    try:
        x_null = np.arange(-mgrid_size, mgrid_size, 0.001, dtype=float)
        denom = mu * (1 - x_null**2)
        with np.errstate(divide='ignore', invalid='ignore'):
            y_null = np.where(np.abs(denom) > 1e-12, x_null / denom, np.nan)
        # convert any infinities/nans to None in lists
        x_null_list = [float(x) for x in x_null.tolist()]
        y_null_list = [(None if (isinstance(v, float) and (np.isnan(v) or np.isinf(v))) else float(v)) for v in y_null.tolist()]
    except Exception:
        x_null_list = []
        y_null_list = []
        messages.append("nullcline calculation failed")
    # Prepare outputs as built-in types (lists, floats, ints, dicts)
    try:
        t_list = (np.array(t_eval, dtype=float)).tolist() if hasattr(t_eval, "tolist") or isinstance(t_eval, np.ndarray) else list(t_eval)
    except Exception:
        try:
            t_list = list(map(float, t_eval))
        except Exception:
            t_list = []
    if solution is not None and hasattr(solution, "y"):
        try:
            x_traj = [float(v) for v in np.array(solution.y[0], dtype=float).tolist()]
            y_traj = [float(v) for v in np.array(solution.y[1], dtype=float).tolist()]
        except Exception:
            x_traj = []
            y_traj = []
    else:
        x_traj = []
        y_traj = []
    # Convert grids to nested lists
    try:
        x_grid_list = (np.array(x_grid)).tolist()
        y_grid_list = (np.array(y_grid)).tolist()
        u_grid_list = (np.array(u_grid)).tolist()
        v_grid_list = (np.array(v_grid)).tolist()
    except Exception:
        x_grid_list = []
        y_grid_list = []
        u_grid_list = []
        v_grid_list = []
        messages.append("could not convert grids to lists")
    # Optional plotting (default False). If user requests plotting, attempt it.
    plot_requested = bool(params.get("plot", False))
    plot_shown = False
    plot_message = ""
    if plot_requested:
        try:
            import matplotlib.pyplot as plt
            try:
                plt.figure(figsize=(6, 6))
                plt.clf()
                speed = np.sqrt(np.array(u_grid) ** 2 + np.array(v_grid) ** 2)
                density = float(params.get("density", 2.0))
                cmap = params.get("cmap", "cool")
                plt.streamplot(x_grid, y_grid, u_grid, v_grid, color=speed, cmap=cmap, density=density)
                # plot nullclines
                plt.plot(x_null_list, y_null_list, '.', c="darkturquoise", markersize=2)
                plt.plot(x_null_list, [0.0]*len(x_null_list), '.', c="darkturquoise", markersize=2)
                if x_traj and y_traj:
                    plt.plot(x_traj, y_traj, 'r-', lw=3, label=f'Trajectory for mu={mu} and z0={z0}')
                    # start and end points if available
                    plt.plot(x_traj[0], y_traj[0], 'bo', label='start point', alpha=0.75, markersize=7)
                    plt.plot(x_traj[-1], y_traj[-1], 'o', c="yellow", label='end point', alpha=0.75, markersize=7)
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
                # If running in an environment that can show, show. Otherwise save if path provided.
                if isinstance(params.get("savefig"), str):
                    try:
                        plt.savefig(params.get("savefig"))
                        plot_message = f"Figure saved to {params.get('savefig')}"
                    except Exception as e:
                        plot_message = f"savefig failed: {e}"
                else:
                    try:
                        plt.show()
                        plot_shown = True
                    except Exception:
                        # Some headless environments may not display; fallback to close
                        plt.close()
                        plot_message = "plt.show() could not display (headless); figure closed"
                plot_shown = plot_shown or ("saved" in plot_message)
            except Exception as e:
                plot_message = f"plotting failed: {e}"
                messages.append(plot_message)
        except Exception as e:
            plot_message = f"matplotlib import failed: {e}"
            messages.append(plot_message)
    # Build result dictionary with only built-in types
    result = {
        "success": bool(sol_success),
        "solver_message": sol_message,
        "t": list(map(float, t_list)) if isinstance(t_list, (list, tuple)) else [],
        "x": list(map(float, x_traj)) if isinstance(x_traj, (list, tuple)) else [],
        "y": list(map(float, y_traj)) if isinstance(y_traj, (list, tuple)) else [],
        "x_grid": x_grid_list,
        "y_grid": y_grid_list,
        "u_grid": u_grid_list,
        "v_grid": v_grid_list,
        "x_null": x_null_list,
        "y_null": y_null_list,
        "mu": float(mu),
        "z0": [float(z0[0]), float(z0[1])],
        "t_span": [float(t_span[0]), float(t_span[1])],
        "t_eval_length": len(t_list),
        "grid_points": int(grid_points),
        "mgrid_size": float(mgrid_size),
        "plot_requested": bool(plot_requested),
        "plot_shown_or_saved": bool(plot_shown),
        "plot_message": str(plot_message),
        "messages": list(messages)
    }
    return result