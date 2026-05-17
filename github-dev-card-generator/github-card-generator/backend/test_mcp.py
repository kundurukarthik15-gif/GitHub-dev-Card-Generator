import asyncio
import os
import json
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card
from dotenv import load_dotenv

load_dotenv()

async def test_end_to_end():
    username = "torvalds"
    print(f"--- Step 1: Scraping GitHub for {username} ---")
    try:
        github_data = await scrape_github(username)
        if "error" in github_data:
            print(f"Error in scrape_github: {github_data['error']}")
            return
        print("Scrape successful.")
    except Exception as e:
        print(f"Failed to scrape GitHub: {str(e)}")
        return

    print(f"\n--- Step 2: Analyzing profile for {username} ---")
    try:
        analysis = await analyze_profile(github_data)
        print("Analysis successful.")
    except Exception as e:
        print(f"Failed to analyze profile: {str(e)}")
        return

    print(f"\n--- Step 3: Generating HTML card ---")
    try:
        html = await generate_card_html(username, github_data, analysis)
        print("Card HTML generated successfully.")
    except Exception as e:
        print(f"Failed to generate card HTML: {str(e)}")
        return

    print(f"\n--- Results ---")
    print(f"Card Theme: {analysis.get('card_theme')}")
    print(f"Developer Vibe: {analysis.get('developer_vibe')}")
    
    # Optional: Save it to see the path
    path = await save_card(username, html)
    print(f"Card saved to: {path}")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
