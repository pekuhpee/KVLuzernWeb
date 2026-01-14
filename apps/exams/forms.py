from django import forms
from django.core.exceptions import ValidationError
from apps.exams.models import ContentItem, MetaOption, UploadBatch
from apps.exams.security import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, validate_uploaded_file
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
        allowed = ", ".join(sorted(f".{ext}" for ext in ALLOWED_EXTENSIONS))
        max_mb = int(MAX_FILE_SIZE / (1024 * 1024))
        self.fields["file"].help_text = f"Erlaubt: {allowed}. Maximal {max_mb} MB."

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file
        try:
            validate_uploaded_file(file)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc
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
