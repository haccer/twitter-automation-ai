import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

# Define project root relative to this file's location (src/core/config_loader.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / 'config'
DEFAULT_SETTINGS_FILE = CONFIG_DIR / 'settings.json'
DEFAULT_ACCOUNTS_FILE = CONFIG_DIR / 'accounts.json'

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, settings_file: Union[str, Path] = DEFAULT_SETTINGS_FILE, 
                 accounts_file: Union[str, Path] = DEFAULT_ACCOUNTS_FILE):
        """
        Initializes the ConfigLoader.

        Args:
            settings_file (Union[str, Path], optional): Path to the settings JSON file. 
                                                        Defaults to 'config/settings.json'.
            accounts_file (Union[str, Path], optional): Path to the accounts JSON file. 
                                                        Defaults to 'config/accounts.json'.
        """
        self.settings_file: Path = Path(settings_file)
        self.accounts_file: Path = Path(accounts_file)
        
        self.settings: Dict[str, Any] = self._load_json(self.settings_file, default_value={})
        self.accounts: List[Dict[str, Any]] = self._load_json(self.accounts_file, default_value=[])
        
        if not self.settings:
            logger.warning(f"Settings file '{self.settings_file}' was not found or is empty/invalid. Using empty settings.")
        if not self.accounts:
            logger.warning(f"Accounts file '{self.accounts_file}' was not found or is empty/invalid. Using empty accounts list.")

    def _load_json(self, file_path: Path, default_value: Union[Dict, List]) -> Any:
        """
        Loads a JSON file.

        Args:
            file_path (Path): The path to the JSON file.
            default_value (Union[Dict, List]): The default value to return if loading fails.

        Returns:
            Any: The loaded JSON data or the default value.
        """
        if not file_path.exists():
            logger.error(f"Configuration file not found: {file_path}")
            return default_value
        if not file_path.is_file():
            logger.error(f"Configuration path is not a file: {file_path}")
            return default_value
            
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Successfully loaded JSON from {file_path}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Could not decode JSON from {file_path}: {e}")
            return default_value
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading {file_path}: {e}")
            return default_value

    def get_settings(self) -> Dict[str, Any]:
        """Returns all loaded settings."""
        return self.settings

    def get_accounts_config(self) -> List[Dict[str, Any]]:
        """Returns all loaded account configurations."""
        return self.accounts

    def get_setting(self, path_str: str, default: Any = None) -> Any:
        """
        Retrieves a setting value using a dot-separated path.

        Args:
            path_str (str): Dot-separated path to the setting (e.g., "logging.level").
            default (Any, optional): Default value if the setting is not found. Defaults to None.

        Returns:
            Any: The setting value or the default.
        """
        keys = path_str.split('.')
        current_level = self.settings
        try:
            for key in keys:
                if isinstance(current_level, dict):
                    current_level = current_level[key]
                else: # Path leads to a non-dict item before all keys are consumed
                    logger.warning(f"Invalid path '{path_str}' at key '{key}'. Expected a dictionary, found {type(current_level)}.")
                    return default
            return current_level
        except KeyError:
            logger.debug(f"Setting '{path_str}' not found. Returning default: {default}")
            return default
        except Exception as e:
            logger.warning(f"Error accessing setting '{path_str}': {e}. Returning default: {default}")
            return default

    def get_api_key(self, service_name: str) -> Optional[str]:
        """Retrieves an API key for a specific service."""
        return self.get_setting(f'api_keys.{service_name}')

    def get_twitter_automation_setting(self, setting_name: str, default: Any = None) -> Any:
        """Retrieves a specific setting from the 'twitter_automation' block."""
        return self.get_setting(f'twitter_automation.{setting_name}', default)

    def get_logging_setting(self, setting_name: str, default: Any = None) -> Any:
        """Retrieves a specific setting from the 'logging' block."""
        return self.get_setting(f'logging.{setting_name}', default)

# Example usage (optional, for testing)
if __name__ == '__main__':
    # Basic logging setup for testing ConfigLoader directly
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create dummy config files for testing if they don't exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DEFAULT_SETTINGS_FILE.exists():
        dummy_settings = {
            "api_keys": {
                "openai_api_key": "sk-your_openai_key_here",
                "another_service_key": "another_key_value"
            },
            "twitter_automation": {
                "media_directory": "data/media",
                "processed_tweets_file": "data/processed_tweets.csv",
                "engagement_options": {
                    "like_probability": 0.8,
                    "reply_probability": 0.3
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "file_handler": {
                    "enabled": True,
                    "path": "logs/app.log"
                }
            }
        }
        with DEFAULT_SETTINGS_FILE.open('w', encoding='utf-8') as f:
            json.dump(dummy_settings, f, indent=4)
        logger.info(f"Created dummy settings file: {DEFAULT_SETTINGS_FILE}")

    if not DEFAULT_ACCOUNTS_FILE.exists():
        dummy_accounts = [
            {"username": "user1", "password": "password1", "active": True},
            {"username": "user2", "password": "password2", "active": False}
        ]
        with DEFAULT_ACCOUNTS_FILE.open('w', encoding='utf-8') as f:
            json.dump(dummy_accounts, f, indent=4)
        logger.info(f"Created dummy accounts file: {DEFAULT_ACCOUNTS_FILE}")

    loader = ConfigLoader()
    
    logger.info(f"All Settings: {loader.get_settings()}")
    logger.info(f"All Accounts: {loader.get_accounts_config()}")
    
    logger.info(f"OpenAI API Key: {loader.get_api_key('openai_api_key')}")
    logger.info(f"NonExistent API Key: {loader.get_api_key('non_existent_key')}") # Test default
    
    logger.info(f"Media Directory: {loader.get_twitter_automation_setting('media_directory')}")
    logger.info(f"Like Probability: {loader.get_twitter_automation_setting('engagement_options.like_probability')}") # Test nested with old method
    
    logger.info(f"Logging Level (old method): {loader.get_logging_setting('level')}")
    
    logger.info("--- Testing generic get_setting ---")
    logger.info(f"Logging Level (new method): {loader.get_setting('logging.level')}")
    logger.info(f"Logging File Path: {loader.get_setting('logging.file_handler.path')}")
    logger.info(f"Like Probability (new method): {loader.get_setting('twitter_automation.engagement_options.like_probability')}")
    logger.info(f"Non-existent deep path: {loader.get_setting('a.b.c.d', 'default_value')}")
    logger.info(f"Path to non-dict: {loader.get_setting('logging.level.sublevel', 'default_value_for_non_dict')}")
    logger.info(f"Path to list item (not supported by this simple getter): {loader.get_setting('accounts.0.username')}") # This won't work as expected

    # Clean up dummy files (optional)
    # DEFAULT_SETTINGS_FILE.unlink(missing_ok=True)
    # DEFAULT_ACCOUNTS_FILE.unlink(missing_ok=True)
    # logger.info("Cleaned up dummy config files.")
