from django import forms
from apps.exams.models import ContentItem, MetaOption, UploadBatch
from apps.ranking.models import Teacher


class ContentItemUploadForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = ["title", "content_type", "year", "subject", "teacher", "program", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = "kv-input"
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = input_class
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = input_class
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
            raise forms.ValidationError("Nur PDF, PNG oder JPG-Dateien sind erlaubt.")
        content_type = getattr(file, "content_type", "")
        if content_type and content_type not in allowed_content_types:
            raise forms.ValidationError("Der Dateityp stimmt nicht mit PDF, PNG oder JPG überein.")
        max_size_mb = 25
        if file.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError("Die Datei ist zu gross. Maximal 25 MB erlaubt.")
        return file


class UploadBatchForm(forms.ModelForm):
    class Meta:
        model = UploadBatch
        fields = ["type_option", "year_option", "subject_option", "teacher", "program_option"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_class = "kv-input"
        required_labels = {
            "type_option": "Typ",
            "year_option": "Jahr",
            "subject_option": "Fach",
            "program_option": "Programm",
            "teacher": "Lehrer",
        }
        option_fields = {
            "type_option": "type",
            "year_option": "year",
            "subject_option": "subject",
            "program_option": "program",
        }
        for field_name, category_key in option_fields.items():
            field = self.fields[field_name]
            field.queryset = MetaOption.objects.filter(
                category__key=category_key,
                category__is_active=True,
                is_active=True,
            ).order_by("sort_order", "label")
            field.required = True
            field.error_messages["required"] = f"Bitte {required_labels[field_name]} wählen."
        teacher_field = self.fields["teacher"]
        teacher_field.queryset = Teacher.objects.order_by("-active", "name")
        teacher_field.required = True
        teacher_field.error_messages["required"] = f"Bitte {required_labels['teacher']} wählen."
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = input_class
                field.empty_label = "Bitte wählen"
            else:
                field.widget.attrs["class"] = input_class

    def save(self, commit=True):
        instance = super().save(commit=False)
        type_option = self.cleaned_data.get("type_option")
        if type_option:
            instance.content_type = type_option.value_key
        if commit:
            instance.save()
        return instance
