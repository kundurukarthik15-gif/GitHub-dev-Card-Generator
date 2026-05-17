import os
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
from dotenv import load_dotenv

load_dotenv()


class GitHubCardAgent:
    async def run_agent(self, username: str, theme: str):
        data = await scrape_github(username)
        if "error" in data:
            return {"error": data["error"]}

        analysis = await analyze_profile(data)
        html = await generate_card_html(username, data, analysis, theme)
        url = await save_card(username, html)

        return {
            "username": username,
            "card_url": url,
            "vibe": analysis.get("developer_vibe"),
            "theme": analysis.get("card_theme"),
        }


github_card_agent = GitHubCardAgent()
