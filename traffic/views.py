from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.views import logout
from django.contrib.auth.views import login
from django.http import HttpResponse
from django.template import RequestContext

import datetime
import json

from utils import *


def home(request):
	
	current_time = datetime.datetime.now()
	current_date = current_time.date()
	dates, events_maps, events_timeline = pullEvents('San Francisco', current_time)
	#return HttpResponse(json.dumps(percentiles), content_type="application/json")
	
	data = {'dates': dates, 'events_maps': events_maps, 'events_timeline': events_timeline}
	return render_to_response('flatlab/admin/main.html', data, context_instance=RequestContext(request))


def splash(request):
	data = {}
	return render_to_response('flatlab/admin/splash.html', data, context_instance=RequestContext(request))
	