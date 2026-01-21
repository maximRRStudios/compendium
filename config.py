from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_CONNECTION_STRING = os.environ.get("DATABASE_CONNECTION_STRING")

API_KEY = os.environ.get("API_KEY")
