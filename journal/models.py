from django.db import models
from django.contrib.auth.models import AbstractUser
from .nlp_utils import analyze_sentiment

# Custom User model
class User(AbstractUser):

    def __str__(self):
        return f"{self.username} <{self.email}>"

# Journal Entry linked to custom User model
class JournalEntry(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journal_entries")
    content = models.TextField()
    sentiment = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)    
    created_at = models.DateTimeField(auto_now_add=True)

    # def save(self, *args, **kwargs):
    #     if not self.sentiment:  # Only run if not already analyzed
    #         result = analyze_sentiment(self.content)
    #         self.sentiment = result["label"]
    #         self.confidence = result["score"]
    #     super().save(*args, **kwargs)
    def save(self, *args, **kwargs):
        if not self.sentiment:  # Only run if not already analyzed
            result = analyze_sentiment(self.content)

            # Handle both list and dict outputs
            if isinstance(result, list) and len(result) > 0:
                result = result[0]

            self.sentiment = result.get("label")
            self.confidence = result.get("score")

        super().save(*args, **kwargs)


    def __str__(self):
        return f"Entry by {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
class JournalPages(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journal_pages")
    pages = models.IntegerField(default=10)

    def __str__(self):
        return f"Journal pages for {self.user.username}: {self.pages}"
