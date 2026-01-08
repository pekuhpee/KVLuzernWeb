from django.db import models


class Teacher(models.Model):
    name = models.CharField(max_length=120)
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.name


class RankingCategory(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.title


class RankingVote(models.Model):
    category = models.ForeignKey(RankingCategory, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["category", "token_hash"], name="unique_vote_per_category_per_token")
        ]
    def __str__(self):
        return f"{self.category} - {self.teacher}"
