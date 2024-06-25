import reflex as rx

from reflex_study.components import loading_icon
from reflex_study.state import State


def action_bar() -> rx.Component:
    """
    TODO: index ページのアクションバーと一部共通化をする
    :return:
    """
    return rx.center(
        rx.vstack(
            rx.chakra.form(
                rx.chakra.form_control(
                    rx.hstack(
                        rx.radix.text_area(
                            placeholder="Type your new documents ..",
                            id="documents",
                            width=["15em", "20em", "45em", "50em", "50em", "50em"],
                            rows="8",
                        ),
                        rx.button(
                            rx.cond(
                                State.processing,
                                loading_icon(height="1em"),
                                rx.text("Send"),
                            ),
                            type="submit",
                        ),
                        align_items="center",
                    ),
                    is_disabled=State.processing,
                ),
                on_submit=State.process_documents,
                reset_on_submit=True,
            ),
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
    )
