"""Builds a FastAPI app from a command registry."""

from fastapi import Depends, FastAPI, HTTPException


def build_api(registry) -> FastAPI:
    """Create a FastAPI app with one POST endpoint per registry entry."""
    app = FastAPI(title="Command API")

    @app.get("/")
    async def index():
        """List all registered commands and their descriptions."""
        return {
            name: {"description": cmd.operation.__doc__, "endpoint": f"/{name}"}
            for name, cmd in registry.items()
        }

    @app.get("/status")
    async def status():
        """Report warmup state for every command. warmed_up=true means the model is cached."""
        return {name: {"warmed_up": cmd.warmed_up} for name, cmd in registry.items()}

    for name, command in registry.items():
        _add_endpoint(app, name, command)

    return app


def _add_endpoint(app, name, command):
    """Register a POST endpoint for a command.

    Params fields (if defined) are exposed as query parameters so callers can
    override per request. Config is system-level and not exposed per-request.
    """
    params_cls = getattr(command, "Params", None)

    if params_cls is not None:
        async def endpoint(data, params=Depends(params_cls)):
            return _safe_run(command, data, params)

        endpoint.__annotations__ = {
            "data": command.Input,
            "params": params_cls,
            "return": command.Output,
        }
    else:
        async def endpoint(data):
            return _safe_run(command, data)

        endpoint.__annotations__ = {"data": command.Input, "return": command.Output}

    endpoint.__doc__ = command.operation.__doc__
    app.post(f"/{name}", response_model=command.Output)(endpoint)


def _safe_run(command, data, params=None):
    """Run a command, converting failures into a clean 503 response."""
    try:
        return command.run(data, params)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"{command.name} unavailable: {e}")
