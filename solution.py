from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
import asyncio
import datetime
import random

# Parámetros
XMPP_DOMAIN      = "localhost"
PASSWORD         = "1234"
REQUEST_INTERVAL = 10

# Definición de periodos de costo
PEAK_PERIODS = [(6, 9), (18, 21)]  # Horas pico: 6–9 y 18–21

def get_period(hour: int):
    for start, end in PEAK_PERIODS:
        if start <= hour < end:
            return "peak"
    return "non-peak"

# Agente Dispositivo Base con petición periódica
class DeviceAgent(Agent):
    class RequestBehaviour(PeriodicBehaviour):
        async def run(self):
            name = str(self.agent.jid).split("@")[0]
            base_h = self.agent.preferred_finish.hour
            h = (base_h + random.choice([-1, 0, 1])) % 24
            body = f"{self.agent.mode}:{h}"
            if hasattr(self.agent, "brightness_pref"):
                b0 = self.agent.brightness_pref
                b = max(10, min(100, b0 + random.randint(-10, 10)))
                body += f":{b}"
            msg = Message(to=f"energymanager@{XMPP_DOMAIN}")
            msg.set_metadata("performative", "request")
            msg.body = body
            await self.send(msg)
            print(f"[{name}] Petición enviada: {body}")

    class ProposalHandler(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if not msg or msg.get_metadata("performative") != "propose":
                return

            name = str(self.agent.jid).split("@")[0]
            parts = msg.body.split(":")

            if len(parts) == 3:
                # Lavadora
                start_h, mode, finish_h = parts
                finish_h = int(finish_h)
                delta = abs(finish_h - self.agent.preferred_finish.hour)
                print(f"[{name}] Propuesta recibida: {mode} a las {start_h}:00, finish={finish_h}:00 (Δt={delta}h)")
                accept = delta <= 2
            else:
                # SmartLightsAgent
                start_h, mode, finish_h, bright = parts
                finish_h = int(finish_h); bright = int(bright)
                delta_t = abs(finish_h - self.agent.preferred_finish.hour)
                delta_b = abs(bright - self.agent.brightness_pref)
                print(f"[{name}] Propuesta recibida: {mode} a las {start_h}:00, finish={finish_h}:00, brillo={bright}% (Δt={delta_t}h, Δb={delta_b}%)")
                accept = (delta_t <= 2 and delta_b <= 20)

            reply = msg.make_reply()
            if accept:
                reply.set_metadata("performative", "accept")
                reply.body = "accept"
                print(f"[{name}] Aceptando propuesta")
            else:
                reply.set_metadata("performative", "reject")
                reply.body = "reject"
                print(f"[{name}] Rechazando propuesta")
            await self.send(reply)

    async def setup(self):
        self.add_behaviour(self.RequestBehaviour(period=REQUEST_INTERVAL))
        self.add_behaviour(self.ProposalHandler())

# Agentes específicos
class WasherAgent(DeviceAgent):
    def __init__(self, jid, password, preferred_finish: datetime.datetime, mode="eco"):
        super().__init__(jid, password)
        self.preferred_finish = preferred_finish
        self.mode = mode

class DishwasherAgent(DeviceAgent):
    def __init__(self, jid, password, preferred_finish: datetime.datetime, mode="eco"):
        super().__init__(jid, password)
        self.preferred_finish = preferred_finish
        self.mode = mode

class SmartLightsAgent(DeviceAgent):
    def __init__(
        self,
        jid,
        password,
        preferred_finish: datetime.datetime,
        mode="normal",
        brightness_pref: int = 80
    ):
        super().__init__(jid, password)
        self.preferred_finish = preferred_finish
        self.mode = mode
        self.brightness_pref = brightness_pref

# Agente Administrador Central de Energía
class EnergyManagerAgent(Agent):
    class ManageBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)
            if not msg or msg.get_metadata("performative") != "request":
                return

            sender = str(msg.sender).split("/")[0]
            parts = msg.body.split(":")
            mode, pref_h = parts[0], int(parts[1])
            now_h = datetime.datetime.now().hour
            period = get_period(now_h)

            if period == "peak":
                start_h = (pref_h - (2 if mode=="eco" else 1) + 3 + random.choice([-1,0,1])) % 24
                mode_suggest = "eco"
            else:
                start_h = (pref_h - (1 if mode=="normal" else 2) + random.choice([-1,0,1])) % 24
                mode_suggest = mode
            finish_h = (start_h + (1 if mode_suggest=="normal" else 2)) % 24

            if len(parts) == 2:
                body = f"{start_h}:{mode_suggest}:{finish_h}"
                print(f"[energymanager] Propuesta a {sender}: start={start_h}, mode={mode_suggest}, finish={finish_h} (period={period})")
            else:
                bright_pref = int(parts[2])
                bright_suggest = max(10, bright_pref - (30 if period=="peak" else 0))
                body = f"{start_h}:{mode_suggest}:{finish_h}:{bright_suggest}"
                print(f"[energymanager] Propuesta a {sender}: start={start_h}, mode={mode_suggest}, finish={finish_h}, brightness={bright_suggest}% (period={period})")

            propose = Message(to=sender)
            propose.set_metadata("performative", "propose")
            propose.body = body
            await self.send(propose)

    async def setup(self):
        self.add_behaviour(self.ManageBehaviour())

# Arranque de todos los agentes
async def main():
    now           = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    wash_finish   = now.replace(hour=22)
    dish_finish   = now.replace(hour=21)
    lights_finish = now.replace(hour=23)

    manager    = EnergyManagerAgent(f"energymanager@{XMPP_DOMAIN}", PASSWORD)
    washer     = WasherAgent      (f"washer@{XMPP_DOMAIN}",     PASSWORD, wash_finish,   mode="normal")
    dishwasher = DishwasherAgent  (f"dishwasher@{XMPP_DOMAIN}", PASSWORD, dish_finish,   mode="eco")
    lights     = SmartLightsAgent (f"lights@{XMPP_DOMAIN}",     PASSWORD, lights_finish, mode="normal", brightness_pref=80)

    await manager.start(auto_register=False)
    await washer.start(auto_register=False);     await asyncio.sleep(0.1)
    await dishwasher.start(auto_register=False); await asyncio.sleep(0.1)
    await lights.start(auto_register=False);     await asyncio.sleep(0.1)

    print("[MAIN] Smart Home MAS iniciado. Cada dispositivo pedirá cada 10 s.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())