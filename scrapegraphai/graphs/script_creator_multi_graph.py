"""
ScriptCreatorMultiGraph Module
"""

from copy import deepcopy
from typing import List, Optional, Type

from pydantic import BaseModel

from ..nodes import GraphIteratorNode, MergeGeneratedScriptsNode
from ..utils.copy import safe_deepcopy
from .abstract_graph import AbstractGraph
from .base_graph import BaseGraph
from .script_creator_graph import ScriptCreatorGraph


class ScriptCreatorMultiGraph(AbstractGraph):
    """
    ScriptCreatorMultiGraph is a scraping pipeline that scrapes a list
    of URLs generating web scraping scripts.
    It only requires a user prompt and a list of URLs.
    Attributes:
        prompt (str): The user prompt to search the internet.
        llm_model (dict): The configuration for the language model.
        embedder_model (dict): The configuration for the embedder model.
        headless (bool): A flag to run the browser in headless mode.
        verbose (bool): A flag to display the execution information.
        model_token (int): The token limit for the language model.
    Args:
        prompt (str): The user prompt to search the internet.
        source (List[str]): The source of the graph.
        config (dict): Configuration parameters for the graph.
        schema (Optional[BaseModel]): The schema for the graph output.
    Example:
        >>> script_graph = ScriptCreatorMultiGraph(
        ...     "What is Chioggia famous for?",
        ...     source=[],
        ...     config={"llm": {"model": "openai/gpt-3.5-turbo"}}
        ...     schema={}
        ... )
        >>> result = script_graph.run()
    """

    def __init__(
        self,
        prompt: str,
        source: List[str],
        config: dict,
        schema: Optional[Type[BaseModel]] = None,
    ):
        self.copy_config = safe_deepcopy(config)
        self.copy_schema = deepcopy(schema)
        super().__init__(prompt, config, source, schema)

    def _create_graph(self) -> BaseGraph:
        """
        Creates the graph of nodes representing the workflow for web scraping and searching.
        Returns:
            BaseGraph: A graph instance representing the web scraping and searching workflow.
        """

        graph_iterator_node = GraphIteratorNode(
            input="user_prompt & urls",
            output=["scripts"],
            node_config={
                "graph_instance": ScriptCreatorGraph,
                "scraper_config": self.copy_config,
            },
            schema=self.copy_schema,
        )

        merge_scripts_node = MergeGeneratedScriptsNode(
            input="user_prompt & scripts",
            output=["merged_script"],
            node_config={"llm_model": self.llm_model, "schema": self.schema},
        )

        return BaseGraph(
            nodes=[
                graph_iterator_node,
                merge_scripts_node,
            ],
            edges=[
                (graph_iterator_node, merge_scripts_node),
            ],
            entry_point=graph_iterator_node,
            graph_name=self.__class__.__name__,
        )

    def run(self) -> str:
        """
        Executes the web scraping and searching process.
        Returns:
            str: The answer to the prompt.
        """

        inputs = {"user_prompt": self.prompt, "urls": self.source}
        self.final_state, self.execution_info = self.graph.execute(inputs)
        return self.final_state.get("merged_script", "Failed to generate the script.")
