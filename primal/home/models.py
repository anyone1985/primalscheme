from __future__ import unicode_literals

import os
import uuid

from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import transaction

from argparse import Namespace
from Bio import SeqIO
from primalrefactor.primal import multiplex


class Job(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        verbose_name='Scheme name')
    email = models.EmailField()
    # file will be saved to MEDIA_ROOT/uploads/2015/01/30
    fasta = models.FileField(
        upload_to='uploads/%Y/%m/%d/',
        help_text="One or more viral reference genomes in FASTA format")
    amplicon_length = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(4000)])
    overlap = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(200)])
    prefix = models.CharField(max_length=100)
    request_time = models.DateTimeField(auto_now_add=True)
    results_path = models.CharField(max_length=255, null=True)
    run_start_time = models.DateTimeField(null=True)
    run_finish_time = models.DateTimeField(null=True)
    run_duration = models.DurationField(null=True)

    @property
    def sequences(self):
        return SeqIO.to_dict(list(SeqIO.parse(self.fasta, 'fasta')))

    @property
    def diagram_path(self):
        return os.path.join(self.results_path, '{}.png'.format(self.prefix))

    @property
    def bed_file_path(self):
        return os.path.join(self.results_path, '{}.bed'.format(self.prefix))

    @property
    def results_url(self):
        from django.urls import reverse
        return reverse('home:job_results', kwargs={'job_id': str(self.id)})

    @property
    def results_absolute_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.results_path)

    def make_results_dir(self):
        if not os.path.exists(self.results_absolute_path):
            os.makedirs(self.results_absolute_path)

    def save(self):
        # derive prefix from name
        prefix = ''.join(c for c in self.name if c.isalpha() or c.isdigit())
        self.prefix = prefix if len(prefix) < 11 else prefix[:11]
        super(Job, self).save()

        # create results dir after first save (need id)
        if not self.results_path:
            self.results_path = 'results/{}/{}'.format(str(self.id)[:1], self.id)  # relative to media root
            self.save()
            self.make_results_dir()

    @transaction.atomic
    def run(self):
        args = Namespace()
        args.f = os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.fasta.name)).encode()
        args.p = self.prefix
        args.amplicon_length = self.amplicon_length
        args.min_overlap = self.overlap
        args.search_space = 40
        args.output_path = self.results_absolute_path
        args.v = False
        args.vvv = False

        regions = multiplex(args)

        for r in regions:
            region = Region.objects.create(
                job=self,
                region_number=r.region_num,
                pool=r.pool
            )
            for i, pair in enumerate(r.candidate_pairs):
                primer_left = Primer.objects.create(
                    direction='LEFT',
                    name=pair.left.name,
                    start=pair.left.start,
                    end=pair.left.end,
                    length=pair.left.length,
                    sequence=pair.left.seq,
                    gc=pair.left.gc,
                    tm=pair.left.tm
                )
                primer_right = Primer.objects.create(
                    direction='RIGHT',
                    name=pair.right.name,
                    start=pair.right.start,
                    end=pair.right.end,
                    length=pair.right.length,
                    sequence=pair.right.seq,
                    gc=pair.right.gc,
                    tm=pair.right.tm
                )
                primer_pair = PrimerPair.objects.create(
                    region=region,
                    primer_left=primer_left,
                    primer_right=primer_right,
                    total_score=pair.total
                )
                if i == 0:
                    region.top_pair = primer_pair
                    region.save()


class Region(models.Model):
    job = models.ForeignKey(
        'Job',
        on_delete=models.CASCADE,
    )
    region_number = models.SmallIntegerField()
    pool = models.SmallIntegerField()
    top_pair = models.ForeignKey(
        'PrimerPair',
        on_delete=models.CASCADE,
        related_name='+',
        null=True
    )


class PrimerPair(models.Model):
    region = models.ForeignKey(
        'Region',
        on_delete=models.CASCADE,
        related_name='primer_pairs'
    )
    primer_left = models.ForeignKey(
        'Primer',
        on_delete=models.CASCADE,
        related_name='primer_pair_from_l'
    )
    primer_right = models.ForeignKey(
        'Primer',
        on_delete=models.CASCADE,
        related_name='primer_pair_from_r'
    )
    total_score = models.FloatField()

    @property
    def trimmed_overlap(self):
        if self.region.region_number == 1:
            return 0
        prev_primer_pair = Region.objects.get(job=self.region.job, region_number=self.region.region_number-1).top_pair
        return prev_primer_pair.primer_right.end - self.primer_left.end - 1

    @property
    def product_length(self):
		return self.primer_right.start - self.primer_left.start + 1

    def delete(self, using=None):
        if self.primer_right:
            self.primer_right.delete()
        if self.primer_left:
            self.primer_left.delete()
        super(PrimerPair, self).delete(using)


class Primer(models.Model):
    direction = models.CharField(max_length=5)
    name = models.CharField(max_length=50)
    start = models.IntegerField()
    end = models.IntegerField()
    length = models.SmallIntegerField()
    sequence = models.CharField(max_length=50)
    gc = models.FloatField()
    tm = models.FloatField()

"""
class Alignment(models.Model):
    primer = models.ForeignKey(
        'Primer',
        on_delete=models.CASCADE,
    )
    start = models.IntegerField()
    end = models.IntegerField()
    length = models.IntegerField()
    score = models.IntegerField()
    aln_query = models.CharField(max_length=50)
    aln_ref = models.CharField(max_length=50)
    aln_ref_comp = models.CharField(max_length=50)
    template_3prime = models.CharField(max_length=50)
    primer_3prime = models.CharField(max_length=50)
    mm_3prime = models.BooleanField()
"""
