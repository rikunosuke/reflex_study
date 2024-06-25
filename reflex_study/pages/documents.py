import reflex as rx
from reflex_study.components import navbar, documents


def index() -> rx.Component:
    return rx.chakra.vstack(
        navbar(),
        rx.hstack(
            rx.heading("Documents"), justify="center", padding_y="4em", height="100%"
        ),
        documents.action_bar(),
        min_height="100vh",
        align_items="stretch",
        spacing="0",
    )
