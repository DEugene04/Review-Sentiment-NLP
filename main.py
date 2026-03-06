from fastapi import FastAPI
from sqlalchemy import text
from database import engine

app = FastAPI()

@app.get("/businesses/{business_id}/dashboard") # Get API route
def dashboard(business_id: str):

    # Get latest run for first impression in dashboard
    latest_run_sql = text("""
        SELECT run_id
        FROM analysis_run
        WHERE business_id = :business_id
        ORDER BY created_at DESC
        LIMIT 1
    """)

    with engine.begin() as conn:
        # only return the first row aka the latest
        run_row = conn.execute(latest_run_sql, {"business_id": business_id}).mappings().first()

    # Error handling if the business haven't run analysis at all
    if not run_row:
        return {"error": "No analysis run found"}

    run_id = run_row["run_id"]

    # KPI query
    # Total reviews and total negative reviews
    kpi_sql = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN sentiment_label='negative' THEN 1 ELSE 0 END) AS negative
        FROM review_analysis
        WHERE run_id = :run_id
    """)

    # Top negative topic
    top_negative_sql = text("""
        SELECT
            t.topic_id,
            t.label,
            COUNT(*) AS n_reviews,
            SUM(CASE WHEN ra.sentiment_label='negative' THEN 1 ELSE 0 END) AS negative_count
        FROM topic t
        JOIN review_analysis ra ON ra.topic_id = t.topic_id
        WHERE t.run_id = :run_id
        GROUP BY t.topic_id, t.label
        ORDER BY negative_count DESC
        LIMIT 1
    """)

    # Top positive topic
    top_positive_sql = text("""
        SELECT
            t.topic_id,
            t.label,
            COUNT(*) AS n_reviews,
            SUM(CASE WHEN ra.sentiment_label='positive' THEN 1 ELSE 0 END) AS positive_count
        FROM topic t
        JOIN review_analysis ra ON ra.topic_id = t.topic_id
        WHERE t.run_id = :run_id
        GROUP BY t.topic_id, t.label
        ORDER BY positive_count DESC
        LIMIT 1
    """)

    with engine.begin() as conn:
        kpi = conn.execute(kpi_sql, {"run_id": run_id}).mappings().first()
        top_neg = conn.execute(top_negative_sql, {"run_id": run_id}).mappings().first()
        top_pos = conn.execute(top_positive_sql, {"run_id": run_id}).mappings().first()

    return {
        "total_reviews": kpi["total"],
        "negative_reviews": kpi["negative"],
        "negative_ratio": round(kpi["negative"] / kpi["total"], 3) if kpi["total"] else 0,
        "top_negative_topic": top_neg,
        "top_positive_topic": top_pos
    }