from django.utils.timezone import now
from django.db.models import Avg
from datetime import timedelta
import calendar

SENTIMENT_MAP = {"positive": 1, "neutral": 0, "negative": -1}

def get_mood_trend(user, period="weekly"):
    today = now().date()

    # Helper: convert sentiment to numeric
    def entry_to_score(entry):
        return SENTIMENT_MAP.get(entry.sentiment, 0)

    if period == "weekly":
        # Start on Sunday
        start = today - timedelta(days=today.weekday() + 1)
        end = start + timedelta(days=6)

        entries = (
            user.journal_entries
            .filter(created_at__date__range=[start, end])
        )

        # Group by day
        trend = []
        for i in range(7):
            day = start + timedelta(days=i)
            day_entries = [entry_to_score(e) for e in entries if e.created_at.date() == day]
            avg = sum(day_entries) / len(day_entries) if day_entries else 0
            trend.append({
                "day": day.strftime("%a"),
                "avg_mood": avg
            })

    elif period == "monthly":
        start = today.replace(day=1)
        end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        entries = user.journal_entries.filter(created_at__date__range=[start, end])

        # Initialize buckets for 4 weeks
        weeks = {
            "Week 1": [],
            "Week 2": [],
            "Week 3": [],
            "Week 4": [],
        }

        for e in entries:
            day = e.created_at.day
            score = entry_to_score(e)

            if 1 <= day <= 7:
                weeks["Week 1"].append(score)
            elif 8 <= day <= 14:
                weeks["Week 2"].append(score)
            elif 15 <= day <= 21:
                weeks["Week 3"].append(score)
            else:  # 22 → end of month
                weeks["Week 4"].append(score)

        # Calculate averages
        trend = []
        for label, scores in weeks.items():
            avg = sum(scores) / len(scores) if scores else 0
            trend.append({
                "week": label,
                "avg_mood": avg
            })


    elif period == "annual":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)

        entries = user.journal_entries.filter(created_at__date__range=[start, end])

        trend = []
        for m in range(1, 13):
            month_entries = [entry_to_score(e) for e in entries if e.created_at.month == m]
            avg = sum(month_entries) / len(month_entries) if month_entries else 0
            trend.append({
                "month": calendar.month_abbr[m],
                "avg_mood": avg
            })

    else:
        raise ValueError("Invalid period. Choose weekly, monthly, or annual.")

    return trend
