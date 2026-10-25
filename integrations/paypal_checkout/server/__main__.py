import os

import uvicorn

from .app import create_asgi

if __name__ == "__main__":
    uvicorn.run(create_asgi(), host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8787")),
                proxy_headers=True, forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"))
