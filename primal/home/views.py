import csv

from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from django_slack import slack_message

from primalrefactor.primal import PoolOverlapException

from .forms import JobForm
from .models import Job
from .utils import messages_to_json

def new_job(request):
    if request.method == 'POST':
        job_form = JobForm(request.POST, request.FILES)
        if job_form.is_valid():
            job = job_form.save()

            try:
                job.run()
                run_error_msg = None
            except PoolOverlapException as e:
                run_error_msg = e.message
                slack_message('home/slack/job_exception.slack', {
                    'job': job,
                    'e': e,
                })
            except Exception as e:
                run_error_msg = "An unexpected exception has occurred: {}".format(e.message)
                slack_message('home/slack/job_exception.slack', {
                    'job': job,
                    'e': e,
                })
            if run_error_msg:
                messages.error(request, run_error_msg)
                json = messages_to_json(request)
                return JsonResponse(json, status=500)

            redirect_path = reverse('home:job_results', kwargs={'job_uuid': str(job.uuid)})
            slack_message('home/slack/job_complete.slack', {
                'job': job,
                'results_absolute_uri': request.build_absolute_uri(redirect_path),
            })

            if request.is_ajax():
                return JsonResponse({'redirect_url': redirect_path})
            else:
                return redirect(job)
        else:
            for nfe in job_form.non_field_errors():
                messages.error(request, nfe)
            json = messages_to_json(request)
            json['errors'] = job_form.errors
            return JsonResponse(json, status=400)

    else:
        job_form = JobForm(initial={'amplicon_length': 400, 'overlap': 50})
    return render(request, 'home/new_job.html', {'job_form': job_form})


def job_results(request, job_uuid):
    job = get_object_or_404(Job, uuid=job_uuid)
    return render(request, 'home/job_results.html', {'job': job})


def job_results_csv(request, job_uuid):

    def format_row(region, primer):
        return [
            primer.name,
            primer.sequence,
            region.pool,
            str(primer.length),
            '{0:.2f}'.format(primer.tm),
            '{0:.2f}'.format(primer.gc),
            str(primer.start),
            str(primer.end)
        ]

    job = get_object_or_404(Job, uuid=job_uuid)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="primers.csv"'

    writer = csv.writer(response)
    writer.writerow(['Primer Name', 'Sequence', 'Pool', 'Length', 'Tm', 'GC%',
                     'Start', 'End'])

    for region in job.region_set.all():
        left = region.top_pair.primer_left
        right = region.top_pair.primer_right
        writer.writerow(format_row(region, left))
        writer.writerow(format_row(region, right))

    return response
