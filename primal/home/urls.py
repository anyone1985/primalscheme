from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from . import views


urlpatterns = [
    url(r'^$', views.new_job, name='new_job'),
    url(r'^jobs/(?P<job_uuid>[-\w]{36})/results/$', views.job_results, name='job_results'),
    url(r'^jobs/(?P<job_uuid>[-\w]{36})/csv/$', views.job_results_csv, name='job_results_csv'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
