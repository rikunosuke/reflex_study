from typing import ClassVar

import reflex as rx
from pydantic.v1 import ConfigDict

from reflex_study.config_state import ConfigState, MODEL_CHOICES

from . import style_attribtues

SYSTEM_CONTENT_MAX_LENGTH = 1000


class ConfigBase(rx.Base):

    model_config = ConfigDict(coerce_numbers_to_str=True)

    def _validate(self) -> tuple[bool, str]:
        raise NotImplementedError

    @rx.var
    def is_valid(self) -> bool:
        return self._validate()[0]

    @rx.var
    def error_message(self) -> str:
        return self._validate()[1]


class Content(ConfigBase):
    value: str = ""

    MAX_LENGTH: ClassVar[int] = 1000

    def _validate(self) -> tuple[bool, str]:
        if self.value == "":
            return False, "Content cannot be empty."
        if len(self.value) > self.MAX_LENGTH:
            return (
                False,
                f"Content must be less than {self.MAX_LENGTH} characters.",
            )
        return True, ""


class Model(ConfigBase):
    value: str = ""

    def _validate(self) -> tuple[bool, str]:
        if self.value not in MODEL_CHOICES:
            return (
                False,
                f"{self.value} is not a valid model. Choose from {MODEL_CHOICES}.",
            )
        return True, ""


class Temperature(ConfigBase):
    enable: bool
    value: float

    MAX_VALUE: ClassVar[float] = 2.0
    MIN_VALUE: ClassVar[float] = 0.0
    STEP: ClassVar[float] = 0.1

    def __init__(self, temperature: float | None):
        super().__init__(
            value=temperature or 0.0,
            enable=temperature is not None,
        )

    def _validate(self) -> tuple[bool, str]:
        if not self.enable:
            return True, ""

        value = self.get_value()
        if self.MIN_VALUE > value > self.MAX_VALUE:
            return (
                False,
                f"Temperature must be between {self.MIN_VALUE} and {self.MAX_VALUE}.",
            )
        return True, ""

    def get_value(self) -> float | None:
        if not self.enable:
            return None

        assert isinstance(
            self.value, float
        ), f"Temperature value must be a float, not {self.value}."
        return self.value


class Seed(ConfigBase):
    enable: bool
    value: int

    MIN_VALUE: ClassVar[int] = 0

    def __init__(self, seed: int | None):
        super().__init__(
            value=seed or 0,
            enable=seed is not None,
        )

    def _validate(self) -> tuple[bool, str]:
        if not self.enable:
            return True, ""

        value = self.get_value()
        if value < self.MIN_VALUE:
            return (
                False,
                f"Seed must be over {self.MIN_VALUE}.",
            )
        return True, ""

    def get_value(self) -> int | None:
        if not self.enable:
            return None

        assert isinstance(
            self.value, int
        ), f"Seed value must be an integer, not {self.value}."
        return self.value


class TopP(ConfigBase):
    enable: bool
    value: float

    MAX_VALUE: ClassVar[float] = 1.0
    MIN_VALUE: ClassVar[float] = 0.0
    STEP: ClassVar[float] = 0.1

    def __init__(self, top_p: float | None):
        super().__init__(
            value=top_p or 0.0,
            enable=top_p is not None,
        )

    def _validate(self) -> tuple[bool, str]:
        if not self.enable:
            return True, ""

        value = self.get_value()
        if value < self.MIN_VALUE or self.MAX_VALUE < value:
            return (
                False,
                f"Top P must be between {self.MIN_VALUE} and {self.MAX_VALUE}.",
            )
        return True, ""

    def get_value(self) -> float | None:
        if not self.enable:
            return None

        assert isinstance(
            self.value, float
        ), f"Top P value must be a float, not {self.value}."
        return self.value


class SystemFormState(rx.State):
    input_content: Content = Content(value="")
    input_model: Model = Model(value="")
    input_temperature: Temperature = Temperature(temperature=0.0)
    input_seed: Seed = Seed(seed=0)
    input_top_p: TopP = TopP(top_p=0.0)

    @rx.var
    def is_valid(self) -> bool:
        return all(
            [
                self.input_content.is_valid,
                self.input_temperature.is_valid,
                self.input_model.is_valid,
                self.input_seed.is_valid,
                self.input_top_p.is_valid,
            ]
        )

    def set_input_content(self, content: str):
        self.input_content.value = content

    def set_input_model(self, model: str):
        self.input_model.value = model

    def set_temperature(self, temperature_values: list[float]):
        assert len(temperature_values) == 1
        self.input_temperature.value = float(temperature_values[0])

    def enable_temperature(self, enable: bool):
        self.input_temperature.enable = enable

    def set_seed(self, seed: str):
        self.input_seed.value = int(seed) if seed.isnumeric() else 0

    def enable_seed(self, enable: bool):
        self.input_seed.enable = enable

    def set_top_p(self, top_p_values: list[float]):
        assert len(top_p_values) == 1
        self.input_top_p.value = float(top_p_values[0])

    def enable_top_p(self, enable: bool):
        self.input_top_p.enable = enable

    async def initialize(self):
        config = await self.get_state(ConfigState)
        self.input_content = Content(value=config.content)
        self.input_model = Model(value=config.model)
        self.input_temperature = Temperature(
            temperature=config.temperature,
        )
        self.input_seed = Seed(seed=config.seed)
        self.input_top_p = TopP(top_p=config.top_p)

    async def save(self):
        config = await self.get_state(ConfigState)
        config.overwrite_config(
            content=self.input_content.value,
            model=self.input_model.value,
            temperature=self.input_temperature.get_value(),
            seed=self.input_seed.get_value(),
            top_p=self.input_top_p.get_value(),
        )


def system_content_form():
    return rx.vstack(
        rx.form.root(
            rx.vstack(
                rx.text_area(
                    value=SystemFormState.input_content.value,
                    label="System Content",
                    placeholder="Enter the content",
                    rows="5",
                    is_invalid=~SystemFormState.input_content.is_valid,
                    on_change=SystemFormState.set_input_content,
                    width="100%",
                    required=True,
                ),
                rx.select(
                    MODEL_CHOICES,
                    value=SystemFormState.input_model.value,
                    on_change=lambda value: SystemFormState.set_input_model(value),
                    label="Model",
                    is_invalid=~SystemFormState.input_model.is_valid,
                    width="100%",
                ),
                rx.vstack(
                    rx.checkbox(
                        checked=SystemFormState.input_temperature.enable,
                        on_change=SystemFormState.enable_temperature,
                        text="Temperature",
                    ),
                    rx.cond(
                        SystemFormState.input_temperature.enable,
                        rx.vstack(
                            rx.text(
                                SystemFormState.input_temperature.value,
                                align="center",
                                width="100%",
                            ),
                            rx.slider(
                                default_value=SystemFormState.input_temperature.value,
                                on_value_commit=SystemFormState.set_temperature,
                                max=Temperature.MAX_VALUE,
                                min=Temperature.MIN_VALUE,
                                step=Temperature.STEP,
                                width="100%",
                            ),
                            width="100%",
                        ),
                    ),
                    width="100%",
                    margin_bottom="1em",
                ),
                rx.vstack(
                    rx.checkbox(
                        checked=SystemFormState.input_seed.enable,
                        on_change=SystemFormState.enable_seed,
                        text="Seed",
                    ),
                    rx.cond(
                        SystemFormState.input_seed.enable,
                        rx.chakra.number_input(
                            value=SystemFormState.input_seed.value,
                            on_change=SystemFormState.set_seed,
                            min_=Seed.MIN_VALUE,
                        ),
                    ),
                    width="100%",
                ),
                rx.vstack(
                    rx.checkbox(
                        checked=SystemFormState.input_top_p.enable,
                        on_change=SystemFormState.enable_top_p,
                        text="Top P",
                    ),
                    rx.cond(
                        SystemFormState.input_top_p.enable,
                        rx.vstack(
                            rx.text(
                                SystemFormState.input_top_p.value,
                                align="center",
                                width="100%",
                            ),
                            rx.slider(
                                default_value=SystemFormState.input_top_p.value,
                                on_value_commit=SystemFormState.set_top_p,
                                max=TopP.MAX_VALUE,
                                min=TopP.MIN_VALUE,
                                step=TopP.STEP,
                                width="100%",
                            ),
                            width="100%",
                        ),
                    ),
                    width="100%",
                    margin_bottom="1em",
                ),
                rx.button(
                    "Save",
                    disabled=~SystemFormState.is_valid,
                    on_click=SystemFormState.save,
                    variant="surface",
                    _hover=rx.cond(
                        SystemFormState.is_valid, style_attribtues.POINTER, {}
                    ),
                ),
            ),
        ),
        width="100%",
        on_mount=SystemFormState.initialize,
    )
