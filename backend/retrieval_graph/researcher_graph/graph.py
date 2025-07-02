"""Researcher graph used in the conversational retrieval system as a subgraph.

This module defines the core structure and functionality of the researcher graph,
which is responsible for generating search queries and retrieving relevant documents.
"""

from typing import cast

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from backend import retrieval
from backend.retrieval_graph.configuration import AgentConfiguration
from backend.retrieval_graph.researcher_graph.state import QueryState, ResearcherState
from backend.utils import load_chat_model
from backend.web_search import create_web_search_tool


async def generate_queries(
    state: ResearcherState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Generate search queries based on the question (a step in the research plan).

    This function uses a language model to generate diverse search queries to help answer the question.

    Args:
        state (ResearcherState): The current state of the researcher, including the user's question.
        config (RunnableConfig): Configuration with the model used to generate queries.

    Returns:
        dict[str, list[str]]: A dictionary with a 'queries' key containing the list of generated search queries.
    """

    class Response(TypedDict):
        queries: list[str]

    configuration = AgentConfiguration.from_runnable_config(config)
    structured_output_kwargs = (
        {"method": "function_calling"} if "openai" in configuration.query_model else {}
    )
    model = load_chat_model(configuration.query_model).with_structured_output(
        Response, **structured_output_kwargs
    )
    messages = [
        {"role": "system", "content": configuration.generate_queries_system_prompt},
        {"role": "human", "content": state.question},
    ]
    response = cast(
        Response, await model.ainvoke(messages, {"tags": ["langsmith:nostream"]})
    )
    return {"queries": response["queries"]}


async def retrieve_documents(
    state: QueryState, *, config: RunnableConfig
) -> dict[str, list[Document]]:
    """Retrieve documents based on a given query using both vector search and web search.

    This function combines results from:
    1. Vector database search (for any ingested documents)
    2. Web search using Tavily (for real-time information)

    Args:
        state (QueryState): The current state containing the query string.
        config (RunnableConfig): Configuration with the retriever used to fetch documents.

    Returns:
        dict[str, list[Document]]: A dictionary with a 'documents' key containing the combined list of retrieved documents.
    """
    all_documents = []
    
    # 1. Try vector database search first (for any ingested documents)
    try:
        with retrieval.make_retriever(config) as retriever:
            vector_docs = await retriever.ainvoke(state.query, config)
            all_documents.extend(vector_docs)
    except Exception as e:
        print(f"Vector search failed for query '{state.query}': {str(e)}")
    
    # 2. Perform web search using Tavily
    try:
        web_search = create_web_search_tool()
        web_docs = web_search.search(
            query=state.query,
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
            include_images=False
        )
        all_documents.extend(web_docs)
    except Exception as e:
        print(f"Web search failed for query '{state.query}': {str(e)}")
    
    return {"documents": all_documents}


def retrieve_in_parallel(state: ResearcherState) -> list[Send]:
    """Create parallel retrieval tasks for each generated query.

    This function prepares parallel document retrieval tasks for each query in the researcher's state.

    Args:
        state (ResearcherState): The current state of the researcher, including the generated queries.

    Returns:
        Literal["retrieve_documents"]: A list of Send objects, each representing a document retrieval task.

    Behavior:
        - Creates a Send object for each query in the state.
        - Each Send object targets the "retrieve_documents" node with the corresponding query.
    """
    return [
        Send("retrieve_documents", QueryState(query=query)) for query in state.queries
    ]


# Define the graph
builder = StateGraph(ResearcherState)
builder.add_node(generate_queries)
builder.add_node(retrieve_documents)
builder.add_edge(START, "generate_queries")
builder.add_conditional_edges(
    "generate_queries",
    retrieve_in_parallel,  # type: ignore
    path_map=["retrieve_documents"],
)
builder.add_edge("retrieve_documents", END)
# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "ResearcherGraph"
