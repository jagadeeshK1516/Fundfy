"""Financial analysis tool — structured financial reasoning via LLM."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult

FINANCIAL_ANALYSIS_PROMPT = """Analyze the following business from a financial perspective.

Business Context: {business_context}
Analysis Type: {analysis_type}

Provide a structured analysis including:
- Key metrics and numbers where possible
- Assumptions made
- Recommendations
- Risk factors"""


class AnalyzeFinancialsArgs(BaseModel):
    """Arguments for analyze_financials tool."""

    business_context: str
    analysis_type: str = "unit_economics"


class AnalyzeFinancialsTool(BaseTool):
    """Perform financial analysis on a business (unit economics, projections, break-even)."""

    name = "analyze_financials"
    description = "Perform financial analysis on a business. Supports: unit_economics, projections, break_even. Returns structured financial insights."
    args_schema = AnalyzeFinancialsArgs

    def __init__(self, llm: Any):
        self._llm = llm

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute financial analysis."""
        args = AnalyzeFinancialsArgs(**kwargs)

        try:
            prompt = FINANCIAL_ANALYSIS_PROMPT.format(
                business_context=args.business_context,
                analysis_type=args.analysis_type,
            )

            messages = [
                SystemMessage(content="You are a financial analyst specializing in startup economics. Provide data-driven analysis."),
                HumanMessage(content=prompt),
            ]

            response = await self._llm.ainvoke(messages)

            return ToolResult(
                success=True,
                data={
                    "analysis": response.content,
                    "analysis_type": args.analysis_type,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Financial analysis failed: {str(e)}")
