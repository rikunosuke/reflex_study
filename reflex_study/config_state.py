import json
import warnings
from functools import cache

import reflex as rx

from rxconfig import CONFIG_FILE_PATH

SYSTEM_CONTENT_KEY = "system_content"
MODEL_KEY = "model"
TEMPERATURE_KEY = "temperature"
SEED_KEY = "seed"
TOP_P_KEY = "top_p"

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
    _default_seed = None
    _default_temperature = None
    _default_top_p = None

    @rx.var
    def config(self) -> dict:
        return get_config()

    def overwrite_config(
        self,
        *,
        content: str,
        model: str,
        temperature: float | None,
        seed: int | None,
        top_p: float | None,
    ):
        config_values = {
            SYSTEM_CONTENT_KEY: content,
            MODEL_KEY: model,
            TEMPERATURE_KEY: temperature,
            SEED_KEY: seed,
            TOP_P_KEY: top_p,
        }
        with CONFIG_FILE_PATH.open("w+") as file:
            json.dump(config_values, file, indent=2, ensure_ascii=False)

        get_config.cache_clear()

    @rx.var
    def content(self) -> str:
        if content := self.config.get(SYSTEM_CONTENT_KEY):
            return content
        return self._default_content

    @rx.var
    def model(self) -> str:
        if model := self.config.get(MODEL_KEY):
            if model in MODEL_CHOICES:
                return model
            warnings.warn(f"Invalid model choice: {model}")

        return self._default_model

    @rx.var
    def temperature(self) -> float | None:
        return self.config.get(TEMPERATURE_KEY, self._default_temperature)

    @rx.var
    def seed(self) -> int | None:
        return self.config.get("seed", self._default_seed)

    @rx.var
    def top_p(self) -> float | None:
        return self.config.get("top_p", self._default_top_p)
