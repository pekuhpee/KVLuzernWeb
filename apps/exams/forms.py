from django import forms

from apps.exams.models import ContentItem


class ContentItemUploadForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = [
            "title",
            "content_type",
            "year",
            "subject",
            "teacher",
            "program",
            "file",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = (
            "w-full rounded border border-gray-300 bg-white p-2 text-sm text-gray-900 "
            "dark:border-gray-600 dark:bg-gray-900 dark:text-white"
        )
        select_class = input_class
        file_class = (
            "w-full rounded border border-gray-300 bg-white p-2 text-sm text-gray-900 "
            "dark:border-gray-600 dark:bg-gray-900 dark:text-white"
        )

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = select_class
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = file_class
            else:
                field.widget.attrs["class"] = input_class
        self.fields["file"].help_text = "PDF, PNG oder JPG. Maximal 25 MB."

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file

        allowed_extensions = {"pdf", "png", "jpg", "jpeg"}
        allowed_content_types = {"application/pdf", "image/png", "image/jpeg"}
        extension = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Nur PDF, PNG oder JPG-Dateien sind erlaubt."
            )

        content_type = getattr(file, "content_type", "")
        if content_type and content_type not in allowed_content_types:
            raise forms.ValidationError(
                "Der Dateityp stimmt nicht mit PDF, PNG oder JPG überein."
            )

        max_size_mb = 25
        if file.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(
                "Die Datei ist zu gross. Maximal 25 MB erlaubt."
            )

        return file
