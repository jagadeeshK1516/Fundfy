"""Tool registry — assembles all tools with dependency injection."""

from typing import Any

from fundfy.documents.generator import DocumentGenerator
from fundfy.memory.engine import MemoryEngine
from fundfy.tools.base import BaseTool
from fundfy.tools.document_tool import GenerateDocumentTool
from fundfy.tools.email_tool import DraftEmailTool
from fundfy.tools.financial_tool import AnalyzeFinancialsTool
from fundfy.tools.memory_tools import QueryMemoryTool, SaveToMemoryTool
from fundfy.tools.research_tools import SearchGrantsTool, SearchInvestorsTool
from fundfy.tools.web_scrape import WebScrapeTool
from fundfy.tools.web_search import WebSearchTool
from fundfy.tools.workstream_tools import CreateWorkstreamTool, UpdateWorkstreamTool


def create_tool_registry(
    llm: Any,
    memory_engine: MemoryEngine,
    document_generator: DocumentGenerator,
) -> dict[str, BaseTool]:
    """Instantiate all tools with their dependencies and return them keyed by name.

    Args:
        llm: The shared LLM instance.
        memory_engine: The memory engine for RAG.
        document_generator: The document generator instance.

    Returns:
        Dictionary mapping tool name to tool instance.
    """
    web_search = WebSearchTool()
    web_scrape = WebScrapeTool()
    save_memory = SaveToMemoryTool(memory_engine=memory_engine)
    query_memory = QueryMemoryTool(memory_engine=memory_engine)
    generate_document = GenerateDocumentTool(document_generator=document_generator)
    create_workstream = CreateWorkstreamTool()
    update_workstream = UpdateWorkstreamTool()
    draft_email = DraftEmailTool(llm=llm)
    analyze_financials = AnalyzeFinancialsTool(llm=llm)
    search_grants = SearchGrantsTool(llm=llm, web_search_tool=web_search)
    search_investors = SearchInvestorsTool(llm=llm, web_search_tool=web_search)

    tools = [
        web_search,
        web_scrape,
        save_memory,
        query_memory,
        generate_document,
        create_workstream,
        update_workstream,
        draft_email,
        analyze_financials,
        search_grants,
        search_investors,
    ]

    return {tool.name: tool for tool in tools}
