"""Entry point — reads host/port from config.toml."""

import uvicorn
from server.config import config

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=False,
    )
