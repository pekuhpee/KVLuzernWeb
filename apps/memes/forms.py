from django import forms

from apps.memes.models import Meme


class MemeUploadForm(forms.ModelForm):
    class Meta:
        model = Meme
        fields = ["image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].widget.attrs.update(
            {
                "class": (
                    "w-full rounded border border-gray-300 bg-white p-2 text-sm text-gray-900 "
                    "dark:border-gray-600 dark:bg-gray-900 dark:text-white"
                )
            }
        )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image:
            return image

        allowed_extensions = {"png", "jpg", "jpeg", "webp"}
        extension = image.name.rsplit(".", 1)[-1].lower() if "." in image.name else ""
        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Nur PNG, JPG, JPEG oder WEBP-Dateien sind erlaubt."
            )

        max_size_mb = 10
        if image.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(
                "Die Datei ist zu gross. Maximal 10 MB erlaubt."
            )

        return image
