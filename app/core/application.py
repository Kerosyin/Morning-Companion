from app.config import Settings


class Application:

    def __init__(self, settings: Settings):
        self.settings = settings

    async def start(self):
        pass

    async def stop(self):
        pass
