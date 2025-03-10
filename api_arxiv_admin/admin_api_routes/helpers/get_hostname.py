import socket
import asyncio

async def get_hostname(ip_address: str, timeout: float = 1.0) -> str:
    try:
        host_name = await asyncio.wait_for(
            asyncio.to_thread(socket.gethostbyaddr, ip_address),
            timeout=timeout
        )
        return host_name[0]
    except (asyncio.TimeoutError, socket.herror):
        return "Hostname could not be resolved"
