from Bio import SeqIO

from django.core.exceptions import ValidationError
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

    def clean(self):
        cleaned_data = super(JobForm, self).clean()
        non_field_errors = []

        references = list(SeqIO.parse(cleaned_data['fasta'], 'fasta'))

        if not 1 <= len(references) <= 10:
            e = ValidationError(
                "Between 1 and 10 reference genomes are required in your fasta file. "
                "We recommend selecting a candidate reference from each lineage of interest, rather than "
                "many similar references.", code='invalid')
            self.add_error('fasta', e)
            non_field_errors.append(e)

        if non_field_errors:
            raise ValidationError(non_field_errors)

        return cleaned_data
