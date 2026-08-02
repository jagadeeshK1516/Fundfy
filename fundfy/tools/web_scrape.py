"""Web scraping tool using httpx + BeautifulSoup."""

from typing import Any

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class WebScrapeArgs(BaseModel):
    """Arguments for web scrape tool."""

    url: str


class WebScrapeTool(BaseTool):
    """Scrape a web page and extract its main text content."""

    name = "web_scrape"
    description = "Scrape a web page URL and extract its main text content. Returns the page title and content."
    args_schema = WebScrapeArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Scrape a URL and extract text content."""
        args = WebScrapeArgs(**kwargs)

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(args.url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Try to find main content
            title = soup.title.string if soup.title else ""
            main_content = soup.find("article") or soup.find("main") or soup.find("body")

            if main_content:
                content = main_content.get_text(separator="\n", strip=True)
            else:
                content = soup.get_text(separator="\n", strip=True)

            # Truncate to 8000 chars for LLM context
            content = content[:8000]

            return ToolResult(
                success=True,
                data={"url": args.url, "title": title, "content": content},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Web scrape failed: {str(e)}")
