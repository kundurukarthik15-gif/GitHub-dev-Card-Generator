import os
import json
import httpx
from google import genai
from dotenv import load_dotenv
from typing import Dict
from collections import Counter

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static", "cards")


async def scrape_github(username: str) -> Dict:
    """Fetch GitHub stats and top repos for a given username."""
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    async with httpx.AsyncClient() as http_client:
        user_resp = await http_client.get(
            f"https://api.github.com/users/{username}", headers=headers
        )
        if user_resp.status_code != 200:
            return {"error": f"User '{username}' not found on GitHub"}

        user_data = user_resp.json()

        repos_resp = await http_client.get(
            f"https://api.github.com/users/{username}/repos?sort=updated&per_page=30",
            headers=headers,
        )
        repos_data = repos_resp.json() if repos_resp.status_code == 200 else []

        sorted_repos = sorted(
            repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True
        )[:6]

        top_repos = []
        languages = []
        for r in sorted_repos:
            top_repos.append(
                {
                    "name": r.get("name"),
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language") or "N/A",
                    "description": r.get("description") or "",
                }
            )
            if r.get("language"):
                languages.append(r["language"])

        lang_counts = Counter(languages).most_common(3)
        top_languages = [lang for lang, _ in lang_counts]

        return {
            "name": user_data.get("name") or username,
            "avatar_url": user_data.get("avatar_url", ""),
            "bio": user_data.get("bio") or "",
            "location": user_data.get("location") or "",
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "top_repos": top_repos,
            "most_used_languages": top_languages,
        }


async def analyze_profile(github_data: Dict) -> Dict:
    """Call Gemini to analyze the profile and determine a developer vibe."""
    prompt = f"""
Analyze this GitHub profile data and return a JSON object:
{json.dumps(github_data)}

The JSON must have exactly these keys:
- developer_vibe: (1 sentence personality description)
- top_skills: (list of 3 skill strings based on repos/bio)
- fun_fact: (something clever inferred from their data)
- card_theme: (one of: "hacker", "builder", "researcher", "designer", "open-source-hero")

Return strictly valid JSON only, no markdown.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "developer_vibe": "A passionate developer building cool things.",
            "top_skills": github_data.get("most_used_languages", ["Code", "Git", "Open Source"]),
            "fun_fact": f"Has {github_data.get('public_repos', 0)} public repositories.",
            "card_theme": "builder",
        }


async def generate_card_html(
    username: str, github_data: Dict, analysis: Dict, theme: str = "dark"
) -> str:
    """Generates a self-contained HTML string for a beautiful dev card."""
    themes = {
        "light": {
            "bg": "#f0f2f5",
            "text": "#111111",
            "card_bg": "rgba(255,255,255,0.9)",
            "border": "rgba(0,0,0,0.1)",
            "tag_bg": "rgba(0,0,0,0.07)",
            "tag_text": "#333333",
            "glow": "rgba(99,102,241,0.2)",
            "stat_bg": "rgba(0,0,0,0.04)",
        },
        "neon": {
            "bg": "#020617",
            "text": "#00ffcc",
            "card_bg": "rgba(0,255,204,0.06)",
            "border": "rgba(0,255,204,0.3)",
            "tag_bg": "rgba(0,255,204,0.15)",
            "tag_text": "#00ffcc",
            "glow": "rgba(0,255,204,0.3)",
            "stat_bg": "rgba(0,255,204,0.05)",
        },
        "dark": {
            "bg": "#0d1117",
            "text": "#f0f6fc",
            "card_bg": "rgba(22,27,34,0.85)",
            "border": "rgba(255,255,255,0.08)",
            "tag_bg": "rgba(88,166,255,0.15)",
            "tag_text": "#58a6ff",
            "glow": "rgba(88,166,255,0.3)",
            "stat_bg": "rgba(255,255,255,0.04)",
        },
    }

    t = themes.get(theme, themes["dark"])

    skills_html = "".join(
        [f'<span class="tag">{s}</span>' for s in analysis.get("top_skills", [])]
    )

    repos_html = "".join(
        [
            f'<li><b>{r["name"]}</b> &nbsp;<span style="opacity:0.6;">({r["stars"]} ⭐ · {r["language"]})</span></li>'
            for r in github_data.get("top_repos", [])[:3]
        ]
    )

    # card_bg_color used by frontend for download background
    bg_color = t['bg']

    html = f"""<style>
  .dev-card {{
    width: 420px;
    padding: 28px;
    border-radius: 24px;
    background: {t['card_bg']};
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {t['border']};
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    color: {t['text']};
    position: relative;
    overflow: hidden;
    font-family: 'Inter', Arial, sans-serif;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }}
  .dev-card:hover {{
    transform: translateY(-6px) scale(1.015);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  }}
  .dev-card .glow {{
    position: absolute;
    top: -80px; right: -80px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, {t['glow']}, transparent 70%);
    pointer-events: none;
  }}
  .dev-card .avatar {{
    width: 76px; height: 76px;
    border-radius: 50%;
    border: 3px solid {t['border']};
    object-fit: cover;
  }}
  .dev-card .header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }}
  .dev-card .name {{ font-size: 1.25rem; font-weight: 800; }}
  .dev-card .handle {{ opacity: 0.6; font-size: 0.9rem; margin-top: 2px; }}
  .dev-card .bio {{ line-height: 1.6; opacity: 0.85; font-size: 0.92rem; margin-bottom: 16px; }}
  .dev-card .vibe {{ font-style: italic; opacity: 0.9; line-height: 1.6; font-size: 0.92rem; margin-bottom: 18px; }}
  .dev-card .tags {{ margin-bottom: 18px; }}
  .dev-card .tag {{
    display: inline-block;
    padding: 5px 12px; margin: 3px;
    background: {t['tag_bg']};
    color: {t['tag_text']};
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
  }}
  .dev-card .stats {{
    display: flex;
    justify-content: space-around;
    padding: 14px;
    border-radius: 14px;
    background: {t['stat_bg']};
    margin-bottom: 18px;
    font-size: 0.88rem;
  }}
  .dev-card .stat-item {{ text-align: center; }}
  .dev-card .stat-value {{ font-size: 1.2rem; font-weight: 800; }}
  .dev-card .stat-label {{ opacity: 0.6; font-size: 0.75rem; margin-top: 2px; }}
  .dev-card .repos-title {{ font-weight: 700; margin-bottom: 10px; font-size: 0.9rem; }}
  .dev-card ul {{ padding-left: 18px; line-height: 1.8; font-size: 0.88rem; }}
  .dev-card .fun-fact {{
    font-size: 0.82rem;
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid {t['border']};
    opacity: 0.8;
    line-height: 1.5;
  }}
</style>
<div class="dev-card" data-bg="{bg_color}">
  <div class="glow"></div>
  <div class="header">
    <img class="avatar" src="{github_data.get('avatar_url')}" alt="avatar">
    <div>
      <div class="name">{github_data.get('name')}</div>
      <div class="handle">@{username}</div>
      {f'<div style="font-size:0.78rem;opacity:0.6;margin-top:3px;">📍 {github_data.get("location")}</div>' if github_data.get("location") else ""}
    </div>
  </div>
  {f'<p class="bio">{github_data.get("bio")}</p>' if github_data.get("bio") else ""}
  <p class="vibe">"{analysis.get('developer_vibe', '')}"</p>
  <div class="tags">{skills_html}</div>
  <div class="stats">
    <div class="stat-item">
      <div class="stat-value">{github_data.get('public_repos', 0)}</div>
      <div class="stat-label">Repos</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">{github_data.get('followers', 0)}</div>
      <div class="stat-label">Followers</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">{len(github_data.get('most_used_languages', []))}</div>
      <div class="stat-label">Languages</div>
    </div>
  </div>
  <div class="repos-title">🔥 Top Projects</div>
  <ul>{repos_html}</ul>
  <p class="fun-fact"><b>💡 Fun Fact:</b> {analysis.get('fun_fact', '')}</p>
</div>"""
    return html


async def save_card(username: str, html: str) -> str:
    """Saves the card as a standalone HTML file and returns the relative URL path."""
    os.makedirs(STATIC_DIR, exist_ok=True)
    file_path = os.path.join(STATIC_DIR, f"{username}.html")
    # Wrap the snippet in a full page for the saved file
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{username} | Dev Card</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 30px; }}
</style>
</head>
<body>
{html}
</body>
</html>"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return f"/static/cards/{username}.html"
