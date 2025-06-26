from django import forms

class DuplicateWorkoutForm(forms.Form):
    n = forms.ChoiceField(
        label="Количество копий",
        choices=[(i, str(i)) for i in range(1, 31)],
        initial=5
    )
    k = forms.ChoiceField(
        label="Интервал в днях",
        choices=[(i, str(i)) for i in range(1, 8)],
        initial=1
    )
