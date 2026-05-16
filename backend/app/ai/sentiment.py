from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(description: str) -> str:
    score = analyzer.polarity_scores(description)

    compound = score["compound"]

    if compound >= 0.5:
        return "positive"

    if compound <= -0.3:
        return "negative"

    return "neutral"