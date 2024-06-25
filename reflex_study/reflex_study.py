"""The main Chat app."""

import reflex as rx
from reflex_study.pages import index
from reflex_study.pages import documents

# Add state and page to the app.
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="violet",
    ),
)

app.add_page(index.index)
app.add_page(documents.index, route="/documents")
