from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from apps.exams.models import MetaOption, UploadBatch, UploadFile
from apps.ranking.models import Teacher
class UploadBatchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(self.user)
        self.teacher = Teacher.objects.create(name="Test Lehrer")
    def _create_batch(self):
        option_ids = {f"{key}_option": MetaOption.objects.filter(category__key=key).values_list("id", flat=True).first()
                      for key in ["type", "year", "subject", "program"]}
        option_ids["teacher"] = self.teacher.id
        response = self.client.post(reverse("exams:create_upload_batch"), data=option_ids)
        return response.json()["batch_id"]
    def test_rejects_too_many_files(self):
        batch_id = self._create_batch()
        files = [
            SimpleUploadedFile(f"file-{i}.txt", b"hi", content_type="text/plain")
            for i in range(11)
        ]
        response = self.client.post(
            reverse("exams:upload_batch_files", args=[batch_id]),
            data={"files": files},
        )
        self.assertEqual(response.status_code, 400)
    def test_rejects_invalid_type(self):
        batch_id = self._create_batch()
        bad_file = SimpleUploadedFile("file.exe", b"bad", content_type="application/octet-stream")
        response = self.client.post(
            reverse("exams:upload_batch_files", args=[batch_id]),
            data={"files": [bad_file]},
        )
        self.assertEqual(response.status_code, 400)
    def test_rejects_too_large_file(self):
        batch_id = self._create_batch()
        big_file = SimpleUploadedFile(
            "big.pdf",
            b"x" * (15 * 1024 * 1024 + 1),
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("exams:upload_batch_files", args=[batch_id]),
            data={"files": [big_file]},
        )
        self.assertEqual(response.status_code, 400)
    def test_download_zip_headers(self):
        batch = UploadBatch.objects.create(owner=self.user, status=UploadBatch.Status.APPROVED)
        upload_file = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
        UploadFile.objects.create(
            batch=batch,
            file=upload_file,
            original_name="test.txt",
            size=5,
            mime="text/plain",
        )
        response = self.client.get(reverse("exams:download_upload_batch", args=[batch.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("attachment;", response["Content-Disposition"])
