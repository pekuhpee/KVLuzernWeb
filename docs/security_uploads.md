# Upload security measures

This project applies the following controls around Prü­fungen/Lernstoff uploads and ZIP downloads:

- **Allowlisted file types**: uploads are limited to PDF, Office docs, images, and ZIP archives.
- **Server-side validation**: both extension and MIME type are checked; files larger than the size limit are rejected.
- **ZIP inspection on upload**: ZIP archives are scanned to reject path traversal entries and executable extensions.
- **ZipSlip prevention on download**: ZIP filenames are sanitized to basename-only and normalized with `get_valid_filename` before streaming.
- **Pending until approved**: uploads remain in `PENDING` status until an admin approves them; only approved batches are shown publicly.
- **Safe download headers**: ZIP and file downloads set `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`.

If any of the above checks are adjusted, ensure they remain aligned with the validation in `apps/exams/views.py`.
