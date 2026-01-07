from django.db import models


class ContentItem(models.Model):
    class ContentType(models.TextChoices):
        EXAM = "EXAM", "Exam"
        MATERIAL = "MATERIAL", "Material"

    class Program(models.TextChoices):
        BM = "BM", "BM"
        LEHRE = "LEHRE", "Lehre"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    title = models.CharField(max_length=200)
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.EXAM,
    )
    year = models.IntegerField(null=True, blank=True)
    subject = models.CharField(max_length=120)
    teacher = models.CharField(max_length=120, blank=True)
    program = models.CharField(
        max_length=20,
        choices=Program.choices,
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to="content/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.title
