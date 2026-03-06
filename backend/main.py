from fastapi import FastAPI
from sqlalchemy import text
from database import engine
from fastapi.middleware.cors import CORSMiddleware
from import_reviews import router as import_router
from run_analysis import router as run_analysis_router

# Allowing CORS
app = FastAPI()
app.include_router(import_router)
app.include_router(run_analysis_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {'status': 'ok', 'message': 'backend is working'}

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

@app.get("/businesses/{business_id}/get_reviews") # Get API route for getting reviews
def dashboard(business_id: str):

    get_reviews_query = text(
        """
        SELECT r.text as Reviews, t.label as Topic, ra.sentiment_label as Label
        FROM review r
        JOIN review_analysis ra ON r.review_id = ra.review_id
        JOIN topic t ON t.topic_id = ra.topic_id
        WHERE r.business_id = :business_id
        """
    )

    with engine.begin() as conn:
        get_reviews = conn.execute(get_reviews_query, {"business_id": business_id}).mappings().all()

    if not get_reviews:
        return {"error": "No analysis run found"}
    
    return {"reviews": get_reviews}