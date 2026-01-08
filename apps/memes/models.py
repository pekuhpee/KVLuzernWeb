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
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Keep the default manager unfiltered so admin can review all uploads.
    objects = models.Manager()
    approved = ApprovedMemeManager()

    def __str__(self):
        return f"Meme {self.pk} ({self.status})"
