import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.amazon.co.uk/s?k=tshirts+men+uk&crid=1D778CVHWJLYO&sprefix=tshirts+%2Caps%2C73&ref=nb_sb_ss_mvt-t11-ranker_1_8",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())