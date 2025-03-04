import socket
import asyncio

async def get_hostname(ip_address: str, timeout: float = 1.0) -> str:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(socket.gethostbyaddr, ip_address),
            timeout=timeout
        )
    except (asyncio.TimeoutError, socket.herror):
        return "Hostname could not be resolved"
