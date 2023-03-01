
import asyncio
from mcstatus import JavaServer


servers = {
    JavaServer.lookup("hypixel.net"): "pickle",
    JavaServer.lookup("mineplex.com"): "mp",
    JavaServer.lookup("funcraft.net"): "fc",
    JavaServer.lookup("pactify.fr"): "pac"
}

        # "CubeKrowd": "cubekrowd.net",
        # "Funcraft": "funcraft.net",
        # "Pactify": "pactify.fr",

async def ntm(serv: JavaServer, nm: str):
    print(nm + ": " + str((await serv.async_status()).players.online))


async def get_all():
    tasks = []
    for server, nom in servers.items():
        tasks.append(ntm(server, nom))
    print("all started")

    await asyncio.gather(*tasks)
    print("=== all done ===")
    await asyncio.sleep(2)

while True:
    asyncio.run(get_all())
