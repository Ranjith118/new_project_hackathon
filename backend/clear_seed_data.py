"""Remove all old seeded/simulated sensor data, keeping only manually entered readings."""
import asyncio
from sqlalchemy import delete, text
from app.database import engine, Base

async def clear():
    async with engine.begin() as conn:
        # Delete ALL sensor data rows - user will enter fresh manual data
        result = await conn.execute(text("DELETE FROM sensor_data"))
        print(f"Deleted {result.rowcount} sensor data rows")
    print("Done. The sensor data table is now empty.")
    print("Go to the Sensor Data page and enter readings manually.")

asyncio.run(clear())
