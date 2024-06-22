import json
import warnings
from functools import cache

import reflex as rx

from rxconfig import CONFIG_FILE_PATH

SYSTEM_CONTENT_KEY = "system_content"
MODEL_KEY = "model"
TEMPERATURE_KEY = "temperature"

MODEL_CHOICES = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]


@cache
def get_config() -> dict:
    with CONFIG_FILE_PATH.open("r") as file:
        try:
            config = json.load(file)
        except json.JSONDecodeError:
            return {}
    if not isinstance(config, dict):
        warnings.warn(f"Config file is not a dictionary: {config}")
        return {}
    return config


class ConfigState(rx.State):
    _default_content = "You are a friendly chatbot named Reflex. Respond in markdown."
    _default_model = "gpt-4o"
    _default_temperature = 0.0
    set_seed: bool = False
    set_temperature: bool = False

    @rx.var
    def config(self) -> dict:
        return get_config()

    def _set_config_value(self, config_values) -> None:
        config = get_config()
        with CONFIG_FILE_PATH.open("w+") as file:
            for key, new_value in config_values.items():
                config[key] = new_value
            json.dump(config, file, indent=2, ensure_ascii=False)

        get_config.cache_clear()

    def set_config(self, *, content: str, model: str, temperature: float | None):
        self._set_config_value(
            config_values={
                SYSTEM_CONTENT_KEY: content,
                MODEL_KEY: model,
                TEMPERATURE_KEY: temperature,
            }
        )

    @rx.var
    def content(self) -> str:
        return self.config.get(SYSTEM_CONTENT_KEY, self._default_content)

    @rx.var
    def model(self) -> str:
        return self.config.get(MODEL_KEY, self._default_model)

    @rx.var
    def temperature(self) -> float:
        return self.config.get(TEMPERATURE_KEY, self._default_temperature)
