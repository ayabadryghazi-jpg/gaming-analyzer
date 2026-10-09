import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Fortnite Performance Analyzer Backend is working!",
        "supabase": "connected"
    }


@app.get("/matches")
def get_matches():
    try:
        response = supabase.table("matches").select("*").limit(10).execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}


def fetch_matches():
    response = supabase.table("matches").select("*").limit(100).execute()
    return response.data


@app.get("/stats")
def get_stats():
    try:
        matches = fetch_matches()
        if not matches:
            return {"error": "No matches yet"}

        n = len(matches)
        total_kills = sum(m.get("eliminations") or 0 for m in matches)
        total_deaths = sum(m.get("deaths") or 0 for m in matches)

        return {
            "matches": n,
            "wins": sum(1 for m in matches if m.get("is_win")),
            "win_rate": round(100 * sum(1 for m in matches if m.get("is_win")) / n, 1),
            "top10_rate": round(100 * sum(1 for m in matches if (m.get("placement") or 999) <= 10) / n, 1),
            "avg_eliminations": round(total_kills / n, 2),
            "kd_ratio": round(total_kills / max(total_deaths, 1), 2),
            "avg_damage": round(sum(m.get("damage") or 0 for m in matches) / n, 1),
            "avg_accuracy": round(sum(float(m.get("accuracy") or 0) for m in matches) / n, 1),
            "avg_survival_minutes": round(sum(m.get("survival_minutes") or 0 for m in matches) / n, 1),
            "avg_placement": round(sum(m.get("placement") or 0 for m in matches) / n, 1),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/recommendations")
def get_recommendations():
    stats = get_stats()
    if "error" in stats:
        return stats

    tips = []
    if stats["avg_accuracy"] < 25:
        tips.append("Your accuracy is low: practice aiming in Creative mode and try lowering your sensitivity.")
    if stats["kd_ratio"] < 1.5:
        tips.append("Your K/D ratio is low: avoid open fights and engage from high ground.")
    if stats["avg_damage"] < 500:
        tips.append("Your damage output is low: take more fights and use a variety of weapons.")
    if stats["avg_survival_minutes"] < 12:
        tips.append("You are dying early: land in quieter areas and follow the storm from the start.")
    if stats["top10_rate"] < 40:
        tips.append("Your Top 10 rate is low: focus on positioning and surviving to the end game.")
    if not tips:
        tips.append("Great performance! Keep pushing and try a higher difficulty level.")

    return {"stats": stats, "recommendations": tips}