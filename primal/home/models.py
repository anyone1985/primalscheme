from __future__ import unicode_literals

import os
import uuid

from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import transaction

from argparse import Namespace
from Bio import SeqIO
from primalscheme.scheme import multiplex


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
    request_time = models.DateTimeField(auto_now_add=True)
    run_start_time = models.DateTimeField(null=True)
    run_finish_time = models.DateTimeField(null=True)
    run_duration = models.DurationField(null=True)
    results_path = models.CharField(max_length=255, null=True)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('home:job_results', kwargs={'job_id': str(self.id)})

    def make_results_dir(self):
        self.results_path = os.path.join(
            settings.MEDIA_ROOT, 'results/%i' % self.id)
        self.save()
        os.makedirs(self.results_path)

    @transaction.atomic
    def run(self):
        self.make_results_dir()

        args = Namespace()
        args.g = os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.fasta.name)).encode()
        args.o = ''
        args.length = self.amplicon_length
        args.overlap = self.overlap

        regions = multiplex(args)

        for r in regions:
            region = Region.objects.create(
                job=self,
                scheme=r.scheme,
                region_number=r.region,
                pool=r.pool
            )
            for i, pair in enumerate(r.pairs):
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

    def generate_bed_file(self):
        records = SeqIO.parse(
            open(os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.fasta.name)), 'r'), 'fasta')
        header = list(records)[0].id

        with open(os.path.join(self.results_path, self.output_prefix + '.bed'), 'w') as bedfile:
            for r in self.region_set.all():
                pair = r.top_pair
                print >> bedfile, '\t'.join([
                    header,
                    str(pair.primer_left.start),
                    str(pair.primer_left.end),
                    str(pair.primer_left.name)
                ])
                print >> bedfile, '\t'.join([
                    header,
                    str(pair.primer_right.start),
                    str(pair.primer_right.end),
                    str(pair.primer_right.name)
                ])


class Region(models.Model):
    job = models.ForeignKey(
        'Job',
        on_delete=models.CASCADE,
    )
    scheme = models.SmallIntegerField()
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
