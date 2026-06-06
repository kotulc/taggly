"""Builds a FastAPI app from a command registry."""

from fastapi import Depends, FastAPI


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

    for name, command in registry.items():
        _add_endpoint(app, name, command)

    return app


def _add_endpoint(app, name, command):
    """Register a single POST endpoint for a command, pulling docs from run.__doc__.

    Config fields are exposed as query parameters so callers can override defaults
    per request. Use the COMMANDS env var to set deployment-level defaults.
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

    endpoint.__doc__ = command.operation.__doc__
    app.post(f"/{name}", response_model=command.Output)(endpoint)
