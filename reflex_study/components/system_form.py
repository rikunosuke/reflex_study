import reflex as rx

from reflex_study.state import State

from . import style_attribtues

SYSTEM_CONTENT_MAX_LENGTH = 1000


class SystemStateForm(rx.State):
    input: str = ""

    @rx.var
    def is_valid_input(self) -> bool:
        return self._validate()[0]

    @rx.var
    def error_message(self) -> str:
        return self._validate()[1]

    def _validate(self) -> tuple[bool, str]:
        if self.input == "":
            return False, "Content cannot be empty."
        if len(self.input) > SYSTEM_CONTENT_MAX_LENGTH:
            return (
                False,
                f"Content must be less than {SYSTEM_CONTENT_MAX_LENGTH} characters.",
            )
        return True, ""

    def initialize(self, new_input: str):
        assert isinstance(new_input, str)
        self.input = new_input


def system_content_form():
    return rx.vstack(
        rx.form.root(
            rx.vstack(
                rx.text_area(
                    value=SystemStateForm.input,
                    label="System Content",
                    placeholder="Enter the content",
                    rows="5",
                    is_invalid=~SystemStateForm.is_valid_input,
                    on_change=SystemStateForm.set_input,
                    width="100%",
                ),
                rx.button(
                    "Save",
                    is_disabled=~SystemStateForm.is_valid_input,
                    on_click=lambda: State.set_content(SystemStateForm.input),
                    variant="surface",
                    _hover=rx.cond(
                        SystemStateForm.is_valid_input, style_attribtues.POINTER, {}
                    ),
                ),
            ),
        ),
        width="100%",
    )
