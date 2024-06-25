import os

import reflex as rx
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_text_splitters import TokenTextSplitter
from openai import OpenAI

from reflex_study.config_state import ConfigState
from reflex_study.langchain_api import LangChainAPI

# Checking if the API key is set properly
if not os.getenv("OPENAI_API_KEY"):
    raise Exception("Please set OPENAI_API_KEY environment variable.")


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


DEFAULT_CHATS = {
    "Intros": [],
}


class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        model = self.openai_process_question

        async for value in model(question):
            yield value

    async def openai_process_question(self, question: str):
        """Get the response from the API.

        Args:
            form_data: A dict with the current question.
        """

        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        # Build the messages.
        messages = []
        for qa in self.chats[self.current_chat][:-1]:
            messages.append({"role": "user", "content": qa.question})
            messages.append({"role": "assistant", "content": qa.answer})

        config_state = await self.get_state(ConfigState)
        llm = await self.get_llm()
        api = LangChainAPI(llm=llm)

        answers = api.aquestion(
            system_content=config_state.content,
            messages=messages,
            question=question,
        )

        # Stream the results, yielding after every word.
        async for answer_text in answers:
            # Ensure answer_text is not None before concatenation
            if answer_text is not None:
                self.chats[self.current_chat][-1].answer += answer_text
            else:
                # Handle the case where answer_text is None, perhaps log it or assign a default value
                # For example, assigning an empty string if answer_text is None
                answer_text = ""
                self.chats[self.current_chat][-1].answer += answer_text
            self.chats = self.chats
            yield

        # Toggle the processing flag.
        self.processing = False

    async def process_documents(self, form_data):
        text: str = form_data["documents"]
        if text == "":
            return
        self.processing = True
        yield

        await self.node4j_processing(text)

        self.processing = False

    async def node4j_processing(self, text: str):
        text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=125)
        documents = text_splitter.create_documents([text])

        llm = await self.get_llm()
        llm_transformer = LLMGraphTransformer(llm=llm)
        graph_documents = await llm_transformer.aconvert_to_graph_documents(
            documents=documents
        )
        graph = Neo4jGraph()
        graph.add_graph_documents(
            graph_documents=graph_documents,
            baseEntityLabel=True,
            include_source=True,
        )
        print(graph_documents)
        print("完了")

    async def get_llm(self):
        config_state: ConfigState = await self.get_state(ConfigState)

        return ChatOpenAI(
            temperature=config_state.temperature,
            model_name=config_state.model,
            seed=config_state.seed,
            top_p=config_state.top_p,
        )
