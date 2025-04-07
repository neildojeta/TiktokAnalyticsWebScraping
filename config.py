import os
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:
    def __init__(self):
        load_dotenv(dotenv_path='conf/.env')
        # URL Configuration
        self.url = os.getenv('URL')
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        

config_manager = ConfigManager()
# print(config_manager.url)
