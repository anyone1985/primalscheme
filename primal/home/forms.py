from django.forms import ModelForm

from .models import Job


class JobForm(ModelForm):
    class Meta:
        model = Job
        exclude = (
            'request_time',
            'run_start_time',
            'run_finish_time',
            'run_duration',
            'results_path')
