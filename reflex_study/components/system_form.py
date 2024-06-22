from decimal import Decimal
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
                f"{self.vaue} is not a valid model. Choose from {MODEL_CHOICES}.",
            )
        return True, ""


class Temperature(ConfigBase):
    value: float

    MAX_VALUE: ClassVar[float] = 2.0
    MIN_VALUE: ClassVar[float] = 0.0
    STEP: ClassVar[float] = 0.1

    def _validate(self) -> tuple[bool, str]:
        if self.value is None:
            return True, ""

        if self.MIN_VALUE > self.value > self.MAX_VALUE:
            return (
                False,
                f"Temperature must be between {self.MIN_VALUE} and {self.MAX_VALUE}.",
            )
        return True, ""

    def increment(self):
        self.value = min(
            float(Decimal(str(self.value)) + Decimal(str(self.STEP))),
            self.MAX_VALUE,
        )

    def decrement(self):
        self.value = max(
            float(Decimal(str(self.value)) - Decimal(str(self.STEP))), self.MIN_VALUE
        )


class SystemStateForm(rx.State):
    input_content: Content = Content(value="")
    input_model: Model = Model(value="")
    input_temperature: Temperature = Temperature(value=0.0)

    @rx.var
    def is_valid(self) -> bool:
        return all(
            [
                self.input_content.is_valid,
                self.input_temperature.is_valid,
            ]
        )

    def set_input_content(self, content_value: str):
        self.input_content.value = content_value

    def set_input_model(self, model_value: str):
        self.input_model.value = model_value

    def increment_temperature(self):
        self.input_temperature.increment()

    def decrement_temperature(self):
        self.input_temperature.decrement()

    async def initialize(self):
        config = await self.get_state(ConfigState)
        self.input_content = Content(value=config.content)
        self.input_model = Model(value=config.model)
        self.input_temperature = Temperature(value=config.temperature)

    async def save(self):
        config = await self.get_state(ConfigState)
        config.set_config(
            content=self.input_content.value,
            model=self.input_model.value,
            temperature=self.input_temperature.value,
        )


def system_content_form():
    return rx.vstack(
        rx.form.root(
            rx.vstack(
                rx.text_area(
                    value=SystemStateForm.input_content.value,
                    label="System Content",
                    placeholder="Enter the content",
                    rows="5",
                    is_invalid=~SystemStateForm.input_content.is_valid,
                    on_change=lambda value: SystemStateForm.set_input_content(value),
                    width="100%",
                ),
                rx.select(
                    MODEL_CHOICES,
                    value=SystemStateForm.input_model.value,
                    on_change=lambda value: SystemStateForm.set_input_model(value),
                    label="Model",
                    is_invalid=~SystemStateForm.input_model.is_valid,
                    width="100%",
                ),
                rx.chakra.number_input(
                    rx.chakra.number_input_field(),
                    rx.chakra.number_input_stepper(
                        rx.chakra.number_increment_stepper(
                            on_click=SystemStateForm.increment_temperature
                        ),
                        rx.chakra.number_decrement_stepper(
                            on_click=SystemStateForm.decrement_temperature
                        ),
                    ),
                    value=SystemStateForm.input_temperature.value,
                    label="Temperature",
                    on_mount=SystemStateForm.initialize,
                    # on_change=lambda value: SystemStateForm.set_input_temperature(
                    #     value
                    # ),
                    is_invalid=~SystemStateForm.input_temperature.is_valid,
                    width="100%",
                    max_=Temperature.MAX_VALUE,
                    min_=Temperature.MIN_VALUE,
                ),
                rx.button(
                    "Save",
                    is_disabled=~SystemStateForm.is_valid,
                    on_click=SystemStateForm.save,
                    variant="surface",
                    _hover=rx.cond(
                        SystemStateForm.is_valid, style_attribtues.POINTER, {}
                    ),
                ),
            ),
        ),
        width="100%",
    )
