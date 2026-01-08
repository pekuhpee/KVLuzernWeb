import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from apps.memes.models import Meme, MemeLike


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MemeLikeTests(TestCase):
    def setUp(self):
        self.meme = Meme.objects.create(
            image=SimpleUploadedFile("meme.jpg", b"file", content_type="image/jpeg"),
            status=Meme.Status.APPROVED,
        )

    def test_unique_constraint_for_like(self):
        visitor_id = uuid.uuid4()
        MemeLike.objects.create(meme=self.meme, visitor_id=visitor_id)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemeLike.objects.create(meme=self.meme, visitor_id=visitor_id)

    def test_like_endpoint_increments_and_blocks_duplicate(self):
        visitor_id = uuid.uuid4()
        response = self.client.post(
            f"/api/memes/{self.meme.id}/like/",
            HTTP_X_VISITOR_ID=str(visitor_id),
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.meme.refresh_from_db()
        self.assertEqual(self.meme.like_count, 1)

        response = self.client.post(
            f"/api/memes/{self.meme.id}/like/",
            HTTP_X_VISITOR_ID=str(visitor_id),
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("already_liked"))
