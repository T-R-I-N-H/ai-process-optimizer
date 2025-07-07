# This file is not strictly necessary if basic logging is configured in main.py
# For more advanced setups, you might define loggers, handlers, and formatters here.
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO, # Default logging level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler() # Output to console
            # logging.FileHandler("app.log") # Output to a file
        ]
    )
    # You can also set specific levels for different modules if needed
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING) # Suppress requests/http client logs
    # Set your custom module log levels
    logging.getLogger("agents").setLevel(logging.DEBUG)
    logging.getLogger("core").setLevel(logging.DEBUG)
    logging.getLogger("services").setLevel(logging.DEBUG)
    logging.getLogger("utils").setLevel(logging.DEBUG)

# Call this function at the very beginning of your application (e.g., in main.py)
# from utils.logger import setup_logging
# setup_logging()