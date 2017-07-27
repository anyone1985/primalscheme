from Bio import SeqIO
from Bio.Alphabet import AlphabetEncoder, _verify_alphabet
from Bio.Alphabet import IUPAC

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import Job


class JobForm(ModelForm):
    class Meta:
        model = Job
        exclude = (
            'prefix',
            'request_time',
            'run_start_time',
            'run_finish_time',
            'run_duration',
            'results_path',
            'primary_reference')

    def clean(self):
        cleaned_data = super(JobForm, self).clean()
        fasta = cleaned_data['fasta']
        non_field_errors = []
        alphabet = AlphabetEncoder(IUPAC.unambiguous_dna, 'N')
        references = list(SeqIO.parse(fasta, 'fasta', alphabet=alphabet))

        if not references:
            e = ValidationError(
                "File does not contain any valid fasta records. Descriptor line "
                "should start with >"
            )
            self.add_error('fasta', e)
            non_field_errors.append(e)
            raise ValidationError(non_field_errors)

        primary_ref = references[0]
        primary_ref_len = len(primary_ref)

        if any(abs(len(r) - primary_ref_len) > 200 for r in references):
            e = ValidationError(
                "One or more of your references is too different in length to "
                "the primary (first) reference. The maximum difference is 200 nt",
                code='invalid')
            non_field_errors.append(e)

        if not 1 <= len(references) <= 10:
            e = ValidationError(
                "Between 1 and 10 reference genomes are required in your fasta file. "
                "We recommend selecting a candidate reference from each lineage "
                "of interest, rather than many similar references.", code='invalid')
            non_field_errors.append(e)

        if any(not _verify_alphabet(r.seq) for r in references):
            e = ValidationError(
                "One or more of your fasta sequences contain invalid nucleotide codes. "
                "The supported alphabet is '{}'. Ambiguity codes and gaps are not "
                "currently supported.".format(alphabet.letters), code='invalid')
            non_field_errors.append(e)

        if non_field_errors:
            raise ValidationError(non_field_errors)

        return cleaned_data
