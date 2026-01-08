from django.db import models


class ApprovedMemeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=self.model.Status.APPROVED)


class Meme(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    image = models.ImageField(upload_to="memes/")
    title = models.CharField(max_length=200, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Keep the default manager unfiltered so admin can review all uploads.
    objects = models.Manager()
    approved = ApprovedMemeManager()

    def __str__(self):
        return f"Meme {self.pk} ({self.status})"


class MemeLike(models.Model):
    meme = models.ForeignKey(Meme, related_name="likes", on_delete=models.CASCADE)
    visitor_id = models.UUIDField()
    ip_hash = models.CharField(max_length=64, blank=True)
    ua_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meme", "visitor_id"], name="unique_meme_like_per_visitor"
            )
        ]

    def __str__(self):
        return f"MemeLike {self.meme_id} by {self.visitor_id}"
