from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from dateutil import parser as dateparser
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import text
from database import engine
import json

router = APIRouter()

TEXT_ALIASES = {'text', 'review', 'content', 'comment', 'komen', 
                'ulasan', 'komentar', 'review_text', 'isi'}
RATING_ALIASES = {'rating', 'stars', 'score', 'nilai', 'bintang'}
DATE_ALIASES =  {'date', 'review_date', 'created_at', 'time', 'tanggal', 'hari'}

import re
def normalize_col(text: str):
    """
    Accepts texts
    Clean input text by:
    - Stripping leading/trailing whitespace
    - Replacing multiple spaces with single space
    - Removing URLs
    """
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'http\S+', '', text)
    text = text.lower()
    return text

def detect_column(cols: List[str], aliases: set[str]):
    # Find exact match with aliases
    for c in cols:
        if c in aliases:
            return c
    # Find words that matches with aliases
    for c in cols:
        if any(a in c for a in aliases):
            return c
    return None

def parse_rating(rating) -> Optional[int]: # Returns either int or none
    if rating is None or (isinstance(rating, float) and pd.isna(rating)):
        return None
    rating_string = str(rating).strip()
    if "/" in rating_string:
        rating_string = rating_string.split('/')[0].strip()
    try:
        # Can handle float and change to integer
        rating_int = int(float(rating_string))
        if 1<= rating_int <= 5:
            return rating_int
        return None
    except:
        return None
    
def parse_date(date) -> Optional[str]:
    if date is None or (isinstance(date, float) and pd.isna(date)):
        return None
    date_string = str(date).strip()
    if not date_string:
        return None
    try:
        datetime = dateparser.parse(date_string, dayfirst=True, fuzzy=True)
        return datetime.date().isoformat()
    except:
        return None
    
@router.post("/businesses/{business_id}/reviews/import/preview")
async def import_preview(business_id: str, file: UploadFile = File(...)):
    # Later if can accept other file than csv modify this line
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a csv file")
    
    df = pd.read_csv(file.file)
    if df.empty:
        raise HTTPException(status_code=400, detail="CSV is empty")
    
    # Normalize and clean all column
    df.columns = [normalize_col(c) for c in df.columns]
    cols_list = list(df.columns)

    text_col = detect_column(cols_list, TEXT_ALIASES)
    rating_col = detect_column(cols_list, RATING_ALIASES)
    date_col = detect_column(cols_list, DATE_ALIASES)

    # The NLP cannot proceed without text
    if not text_col:
        return {
            "ok": False,
            "needs_mapping": True,
            "reason": "Could not detect the review text column",
            "columns": cols_list,
            "suggested_mapping": {"text": None, "rating": rating_col, "review_date": date_col},
        }
    
    rows = []
    errors = []

    for idx, row in df.iterrows():
        # Dictionary are easier to store in JSON and works better with FastAPI
        raw = row.to_dict()
        # If user uploads csv without rating and date col, switch to null
        text = str(raw.get(text_col))
        rating = parse_rating(raw.get(rating_col)) if rating_col else None
        review_date = parse_date(raw.get(date_col)) if date_col else None

        row_errors = []
        if not text_col or text_col.lower() in {'nan', 'none'}:
            row_errors.append('missing_text')
        if rating_col and raw.get(rating_col) is not None and rating is None:
            row_errors.append("invalid_rating")
        if date_col and raw.get(date_col) is not None and review_date is None:
            row_errors.append("invalid_date")

        canonical = {
            "business_id": business_id,
            "source": "upload",
            "rating": rating,
            "text": text,
            "review_date": review_date,
            "extra": {
                "raw": raw,
                "detected_mapping": {
                    "text": text_col,
                    "rating": rating_col,
                    "review_date": date_col
                }
            }
        }
        
        if row_errors:
            errors.append({
                "row_index": int(idx), 
                "errors": row_errors,
                "raw": raw
            })
        else: 
            rows.append(canonical)

    return {
        "ok": True,
        "needs_mapping": False,
        "detected_mapping": {"text": text_col, "rating": rating_col, "review_date": date_col},
        "valid_count": len(rows),
        "error_count": len(errors),
        "preview_valid_rows": rows,
        "preview_errors": errors,
    }

# Define what each review must look like
class CanonicalReview(BaseModel):
    source: str = "upload"
    rating: Optional[int] = None
    text: str
    review_date: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

# Change to list, bcs API expect list
class CommitPayload(BaseModel):
    reviews: List[CanonicalReview]

@router.post("/businesses/{business_id}/reviews/import/commit")
def import_commit(business_id: str, payload: CommitPayload):
    insert_sql = text(
        """
        INSERT INTO review (business_id, source, rating, text, review_date, extra)
        VALUES (:business_id, :source, :rating, :text, :review_date, CAST(:extra AS jsonb))
        RETURNING review_id
        """
    )

    # Bulk insert
    rows = []
    for r in payload.reviews:
        print("ini payload reviews", r)
        rows.append({
            "business_id": business_id,
            "source": r.source,
            "rating": r.rating,
            "text": r.text,
            "review_date": r.review_date,
            "extra": json.dumps(r.extra or {}),
        })

    with engine.begin() as conn:
        print("ini rows payload", rows)
        ids = conn.execute(insert_sql, rows)
    return {ids}