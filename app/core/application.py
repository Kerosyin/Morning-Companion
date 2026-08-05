import asyncio
import logging

from app.core.lifecycle import lifespan

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    """
    Main application entry point.
    """
    async with lifespan(app=None):  # app=None for now
        # The application will run here.
        # For now, it will just start and then immediately shut down.
        # In the future, we will run the bot dispatcher here.
        logging.info("Application is running.")
        # Keep the application running until interrupted
        try:
            # This is a placeholder for the main application loop
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logging.info("Application interrupted.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application stopped by user.")
