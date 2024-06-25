from functools import cached_property
from typing import TypedDict, AsyncIterable

from langchain_community.graphs import Neo4jGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableSerializable,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic.v1 import BaseModel, Field
from langchain_community.vectorstores.neo4j_vector import (
    remove_lucene_chars,
    Neo4jVector,
    SearchType,
)

SYSTEM_ROMPT = """{system_content} Respond in markdown.

context:
{context}
"""


class Message(TypedDict):
    role: str
    content: str


class Entities(BaseModel):
    names: list[str] = Field(
        ...,
        description=(
            "All the person, organization, or business entities that appear in the text"
        ),
    )


class LangChainAPI:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    @cached_property
    def retrieve_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are extracting organization and person entities from the text.",
                ),
                (
                    "human",
                    "Use the given format to extract information from the following "
                    "input: {question}",
                ),
            ]
        )

    @cached_property
    def entity_chain(self) -> RunnableSerializable:
        return self.retrieve_prompt | self.llm.with_structured_output(Entities)

    @cached_property
    def graph(self) -> Neo4jGraph:
        return Neo4jGraph()

    @cached_property
    def vector_index(self) -> Neo4jVector:
        return Neo4jVector.from_existing_graph(
            OpenAIEmbeddings(),
            search_type=SearchType.HYBRID,
            node_label="Document",
            text_node_properties=["text"],
            embedding_node_property="embedding",
        )

    def structured_retriever(self, question: str) -> str:
        """
        Collects the neighborhood of entities mentioned
        in the question
        """
        result = ""
        entities = self.entity_chain.invoke({"question": question})
        for entity in entities.names:
            response = self.graph.query(
                """CALL db.index.fulltext.queryNodes('entity', $query, {limit:20})
                YIELD node,score
                CALL {
                  WITH node
                  MATCH (node)-[r:!MENTIONS]->(neighbor)
                  RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                  UNION ALL
                  WITH node
                  MATCH (node)<-[r:!MENTIONS]-(neighbor)
                  RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
                }
                RETURN output LIMIT 1000
                """,
                {"query": self.generate_full_text_query(entity)},
            )
            result += "\n".join([el["output"] for el in response])
        return result

    def generate_full_text_query(self, entity_name: str) -> str:
        """
        Generate a full-text search query for a given input string.

        This function constructs a query string suitable for a full-text search.
        It processes the input string by splitting it into words and appending a
        similarity threshold (~2 changed characters) to each word, then combines
        them using the AND operator. Useful for mapping entities from user questions
        to database values, and allows for some misspelings.
        """
        full_text_query = ""
        words = [el for el in remove_lucene_chars(entity_name).split() if el]
        for word in words[:-1]:
            full_text_query += f" {word}~2 AND"
        full_text_query += f" {words[-1]}~2"
        return full_text_query.strip()

    def retriever(self, question: str) -> str:
        structured_data = self.structured_retriever(question)
        unstructured_data = [
            el.page_content for el in self.vector_index.similarity_search(question)
        ]
        final_data = f"""Structured data:
        {structured_data}
        Unstructured data:
        {"#Document ". join(unstructured_data)}
        """
        return final_data

    async def aquestion(
        self, system_content: str, messages: list[Message], question: str
    ) -> AsyncIterable[str]:
        system_prompt = SYSTEM_ROMPT.format(
            system_content=system_content, context=self.retriever(question)
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                *[(message["role"], message["content"]) for message in messages],
                ("user", question),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()
        async for msg in chain.astream({}):
            yield msg
