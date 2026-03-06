from sqlalchemy import text
import json

from database import engine

reviews = {}

def run_analysis_pipeline(business_id: str, run_id: str, parameters: dict):
    """
    Function documentation
    - Read reviews from the reviews table based on business_id
    - Cluster topic and compute sentiment
    - Insert new topic rows for this run_id
    - Insert review_analysis row for thid run_id
    """

    # Fetch reviews
    fetch_review_query = text(
        """
        SELECT review_id, rating, text
        FROM review
        WHERE business_id = :business_id
        """
    )
    with engine.begin() as conn:
        reviews = conn.execute(
            fetch_review_query,
            {"business_id": business_id}
        ).mappings().all()

    if not reviews:
        return
    
    # Start of NLP Pipeline
    from sqlalchemy import create_engine
    import pandas as pd
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import re

    # 1. read_reviews_for_business(business_id)
    df_reviews = pd.DataFrame(reviews)
    print(df_reviews.head())

    # 2. Do light cleaning on the text
    def clean_text(text_review):
        text_review = text_review.strip() # remove white spaces before and after the text
        text_review = re.sub(r'\s+', ' ', text_review)
        text_review = re.sub(r'http\S+', '', text_review)  # remove URLs
        return text_review
    df = df_reviews.copy()
    df['text_clean'] = df.text.apply(clean_text)

    # 3. generate_embeddings(reviews)
    model = SentenceTransformer('intfloat/multilingual-e5-small')
    df["input_text"] = df["text_clean"].apply(
        lambda x: "passage: " + x
    )
    embeddings = model.encode(
        df['input_text'].tolist(),
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # 4. cluster_embeddings()
    from sklearn.cluster import KMeans
    k = 6

    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    clusters = kmeans.fit_predict(embeddings)
    df["cluster"] = clusters
    print(df["cluster"].value_counts())

    ## Sanity check cluster
    for i in range(k):
        print(f"\n===== Cluster {i} =====")
        sample_texts = df[df["cluster"] == i]["text"].head(5).tolist()
        for t in sample_texts:
            print("-", t)

    from sklearn.metrics.pairwise import cosine_similarity

    representatives = {}

    ## Finding reviews closest to the centroid and use it to represent the cluster
    for cluster_id in range(k):
        cluster_indices = np.where(df['cluster'] == cluster_id)[0] # Finding which row is True
        cluster_embeddings = embeddings[cluster_indices] # Only select the embeddings of the rows which are true
        centroid = kmeans.cluster_centers_[cluster_id].reshape(1,-1) # Finding the centroid of the cluster and reshaping so that cosine works
        sims = cosine_similarity(cluster_embeddings, centroid).flatten()
        best_idx = cluster_indices[np.argmax(sims)]
        representatives[cluster_id] = df.iloc[best_idx]['text_clean']

    ## Finding top keywrods for each cluster
    from sklearn.feature_extraction.text import TfidfVectorizer
    indonesian_stopwords = [
        "dan", "yang", "untuk", "dengan", "atau", "ini", "itu",
        "karena", "jadi", "tapi", "buat", "saya", "kami", "kita",
        "di", "ke", "dari", "ada", "lebih", "sudah"
    ]
    def top_keywords(texts, n=5):
        v = TfidfVectorizer(max_features=2000, stop_words=indonesian_stopwords)
        X = v.fit_transform(texts) # Vectorize the texts
        words = v.get_feature_names_out() # Getting the vocabulary out
        scores = X.sum(axis=0).A1 # Gives a total TF-IDF score per word
        top_idx = scores.argsort()[-n:][::-1] # Sort indices from smallest to largest, take last n indices, reverse order so highest first
        return [words[i] for i in top_idx]

    cluster_keywords = {}
    cluster_sizes = {}

    for cid in range(k):
        texts = df[df['cluster']==cid]['text_clean'].tolist()
        cluster_sizes[cid] = len(texts)
        cluster_keywords[cid] = top_keywords(texts, 5)

    # 5. label_topics()
    cluster_labels = {}
    for cid in cluster_keywords:
        cluster_labels[cid] = ' / '.join(cluster_keywords[cid][:3])
    df['cluster_label'] = df['cluster'].map(cluster_labels)

    # 6. run_sentiment()
    from transformers import pipeline

    sentiment_model = pipeline(
        'text-classification',
        model = 'w11wo/indonesian-roberta-base-sentiment-classifier',
        device=0
    )

    text_for_sentiment = df['text_clean'].tolist()
    results = sentiment_model(text_for_sentiment, batch_size=16)

    df['sentiment_label_model'] = [r['label'].lower() for r in results]
    df['is_negative'] = (df['sentiment_label_model'] == 'negative').astype(int)
    df['sentiment_score_model'] = [r['score'] for r in results]

    # 7. write_topics_to_db()
    query = text("""
        INSERT INTO topic (run_id, label, keywords, size)
        VALUES (:run_id, :label, :keywords, :size)
        RETURNING topic_id
    """)

    cluster_to_topic_id = {} # Store the topic_id of each cluster

    summary_labels = {}

    for cid in range(k):
        subset = df[df['cluster']==cid]
        size = len(subset)
        avg_rating = subset['rating'].mean()
        neg_ratio = subset['is_negative'].mean()

        impact_score = size * neg_ratio

        summary_labels[cid] = {
            'size': size,
            'avg_rating': round(avg_rating, 2),
            'negative_ratio': round(neg_ratio, 2),
            'impact_score': round(impact_score, 2)
        }

    with engine.begin() as conn: # Opens a transaction
        for cid in range(k):
            label = cluster_labels[cid]
            keywords = cluster_keywords[cid]
            size = summary_labels[cid]['size']
            topic_id = conn.execute(query, {
                'run_id': run_id,
                'label': label,
                'keywords': json.dumps(keywords), # Convert python list to valid JSON
                'size': size
            }).scalar() # Scalar returns the first column of the first row
            cluster_to_topic_id[cid] = topic_id
    
    # Pair each review with its corresponding run_id and topic_id in the review analysis table
    query_review_analysis = text(
        """
        INSERT INTO review_analysis (review_id, run_id, topic_id)
        VALUES (:review_id, :run_id, :topic_id)
        """
    )

    rows = []
    for _, r in df.iterrows():
        rows.append({
            'review_id': r['review_id'],
            'run_id': run_id,
            'topic_id': cluster_to_topic_id[r['cluster']]
    })

    with engine.begin() as conn:
        conn.execute(query_review_analysis, rows)


    # 8. write_review_analysis_to_db()
    update_review_analysis_query = text(
        """
        UPDATE review_analysis
        SET sentiment_label = :sentiment_label,
        sentiment_score = :sentiment_score
        WHERE review_id = :review_id
        AND run_id = :run_id
        """
    )

    payload = []

    for _, r in df.iterrows():
        payload.append({
            "sentiment_label": r['sentiment_label_model'],
            'sentiment_score': r['sentiment_score_model'],
            'review_id': r['review_id'],
            'run_id': run_id
        })

    with engine.begin() as conn:
        conn.execute(update_review_analysis_query, payload)