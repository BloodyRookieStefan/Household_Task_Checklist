import configparser
import copy
import os

from enum import Enum
from ..room import Room
from ..task import Task
from ..logger import get_logger

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.conf")

class LanguageKey(Enum):
    DE = "de"
    EN = "en"

class Config:

    def __init__(self):
        self._users = list()
        self._tasks = dict()
        self._rooms = dict()
        self._language_key = LanguageKey.EN
        self._debug = False
        self._config = None
        self._parse_config()

    def _parse_config(self) -> None:
        """Parses the configuration file and stores it in the instance variable."""
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
        self._config = configparser.ConfigParser()      
        self._config.read(CONFIG_PATH, encoding="utf-8")

        # Set language key
        if "languageKey" in self._config["Settings"]:
            try:
                self._language_key = LanguageKey(self._config["Settings"]["languageKey"])
            except ValueError:
                get_logger(__name__).warning(f"Invalid language key '{self._config['Settings']['languageKey']}' in configuration file. Defaulting to English.")
                self._language_key = LanguageKey.EN
        
        # Get debug mode
        if "debug" in self._config["Settings"]:
            self._debug = self._config["Settings"].getboolean("debug")

    def load(self) -> None:
        """Loads and parses the configuration file."""
        self.get_users()
        self.get_tasks()
        self.get_rooms()

    def get_users(self) -> list[str]:
        """Returns a list of all defined users in the configuration file."""

        if self._users:
            return self._users

        for section in self._config.sections():
            if not section.lower() == "users":
                continue
    
            self._users = [user.strip() for user in self._config[section]["names"].split(",")]
            break

        if len(self._users) == 0:
            raise ValueError("No users found in configuration file.")

        return self._users

    def get_rooms(self) -> dict[str, Room]:
        """Returns all defined rooms"""

        if self._rooms:
            return self._rooms

        # Get tasks first
        if len(self._tasks) == 0:
            self.get_tasks()

        # Parse all rooms from config
        for section in self._config.sections():
            if not section.lower().startswith("room:"):
                continue
            try:
                _room_name = section.split(":")[1]
                _tasks = list()
                for task_name in self._config[section]["tasks"].split(","):
                    if task_name.strip().lower() in self._tasks.keys():
                        _tasks.append(copy.copy(self._tasks[task_name.strip().lower()]))
                    else:
                        get_logger(__name__).warning(f"Task '{task_name.strip()}' not found for room '{_room_name}' in configuration file.")
                self._rooms[_room_name] = Room(name=_room_name, tasks=_tasks)
            except Exception as e:
                get_logger(__name__).error(f"Error parsing room {section}: {e}")

        if len(self._rooms) == 0:
            raise ValueError("No rooms found in configuration file.")

        get_logger(__name__).info(f"Parsed {len(self._rooms)} rooms from configuration file.")

        return self._rooms

    def get_tasks(self) -> dict[str, Task]:
        """Returns all defined tasks"""

        if self._tasks:
            return self._tasks

        # Parse all tasks from config
        for section in self._config.sections():
            if not section.lower().startswith("task:"):
                continue
            try:
                task_name = section.split(":")[1].lower().strip()
                name = self._config[section]["name"]
                repeat = int(self._config[section]["repeat"])
                description = self._config[section]["description"]
                self._tasks[task_name] = Task(name=name, repeat=repeat, description=description)
            except Exception as e:
                get_logger(__name__).error(f"Error parsing task {section}: {e}")

        if len(self._tasks) == 0:
            raise ValueError("No tasks found in configuration file.")
        
        get_logger(__name__).info(f"Parsed {len(self._tasks)} tasks from configuration file.")

        return self._tasks

    def get_full_config(self) -> configparser.ConfigParser:
        """Returns the full configuration as a configparser.ConfigParser object."""
        return self._config

    def get_language_key(self) -> LanguageKey:
        """Returns the language key defined in the configuration file."""
        return self._language_key

    def get_debug_mode(self) -> bool:
        """Returns whether the application is in debug mode based on the configuration file."""
        return self._debug

    def get_config(self, section, key) -> str:
        """Returns the value of a specific configuration key within a section."""
        return self._config[section][key]