"""Builds a FastAPI app from a command registry."""

from fastapi import Depends, FastAPI


def build_api(registry) -> FastAPI:
    """Create a FastAPI app with one POST endpoint per registry entry."""
    app = FastAPI(title="Command API")

    @app.get("/")
    async def index():
        """List all registered commands and their descriptions."""
        return {
            name: {"description": cmd.run.__doc__, "endpoint": f"/{name}"}
            for name, cmd in registry.items()
        }

    for name, command in registry.items():
        _add_endpoint(app, name, command)

    return app


def _add_endpoint(app, name, command):
    """
    Register a single POST endpoint for a command, pulling docs from run.__doc__.

    If the command defines a Config class, its fields are exposed as query parameters
    so callers can override env-resolved defaults on a per-request basis.
    """
    if command.Config is not None:
        async def endpoint(data, config=Depends(command.Config)):
            return command.run(data, config)

        endpoint.__annotations__ = {
            "data": command.Input,
            "config": command.Config,
            "return": command.Output,
        }
    else:
        async def endpoint(data):
            return command.run(data)

        endpoint.__annotations__ = {"data": command.Input, "return": command.Output}

    endpoint.__doc__ = command.run.__doc__
    app.post(f"/{name}", response_model=command.Output)(endpoint)
