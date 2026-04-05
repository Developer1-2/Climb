import asyncio
from main import create_app
from database import SessionLocal
from Services.alerts import send_alerts

async def run_test():
    app = create_app()
    db = SessionLocal()

    await send_alerts(app.bot, db)

if __name__ == "__main__":
    asyncio.run(run_test())