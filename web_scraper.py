import asyncio
import json
import random
from typing import Dict, List, Optional

from google_search_api import GoogleSearchAPI
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


class WebScraper:
    def __init__(self):

        self.google_api = GoogleSearchAPI()

    async def scrape_urls(self, urls: List[str]) -> Optional[Dict]:
        try:
            prune_filter = PruningContentFilter(
                # Lower → more content retained, higher → more content pruned
                threshold=0.05,           
                # "fixed" or "dynamic"
                threshold_type="dynamic",  
                # Ignore nodes with <5 words
                min_word_threshold=5      
            )

            # Step 2: Insert it into a Markdown Generator
            md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

            # Step 3: Pass it to CrawlerRunConfig
            config = CrawlerRunConfig(
                markdown_generator=md_generator
            )
            async with AsyncWebCrawler() as crawler:
                results = await crawler.arun_many(
                    urls=urls,
                    config=config,
                )
            # Process the results
            processed_results = []
            for result in results:
                if result.success:
                    processed_results.append(
                        {
                            "url": result.url,
                            "content": result.markdown.fit_markdown
                        }
                    )
                else:
                    print(f"Failed to scrape {result.url}: {result.error}")
            return processed_results

        except Exception as e:
            print(f"Error scraping {urls}: {e}")
            return None

    async def search_and_scrape(self, query: str, max_results: int = 10) -> List[Dict]:
        # Get search results from Google API
        search_results = await self.google_api.response("web", query, max_results)
        scraped_results = []
        scraped_results = await self.scrape_urls(
            [result["link"] for result in search_results.results]
        )

        return scraped_results


async def main():
    scraper = WebScraper()
    results = await scraper.search_and_scrape("Headache", max_results=10)
    json.dump(results, open("scraped_results.json", "w"), indent=4, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
