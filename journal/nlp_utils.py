from transformers import pipeline

# Load once when Django starts
sentiment_pipeline = pipeline(
    "text-classification",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    # return_all_scores=False
    top_k=1
)

def analyze_sentiment(text: str):
    """Analyze text and return {label, score}"""
    result = sentiment_pipeline(text)[0]
    return result
