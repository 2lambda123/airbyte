# Copyright (c) 2023 Airbyte, Inc., all rights reserved.

import threading
from typing import Any, Type


class Singleton:
    """
    A base class for implementing the Singleton pattern.

    This class stores instances and initialization flags for each subclass in dictionaries.
    This allows each subclass to have its own unique instance and control over its initialization process.

    The __new__ method ensures that only one instance of each subclass is created.
    The _initialized dictionary is used to control when the initialization logic of each subclass is executed.
    """

    _instances: dict[Type["Singleton"], Any] = {}
    _initialized: dict[Type["Singleton"], bool] = {}
    _lock = threading.Lock()

    def __new__(cls: Type["Singleton"], *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                cls._instances[cls] = super().__new__(cls)
                cls._initialized[cls] = False
        return cls._instances[cls]
