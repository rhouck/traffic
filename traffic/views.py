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
	dates, events_maps, events_timeline, percentiles = pullEvents('San Francisco', current_time)
	#return HttpResponse(json.dumps(dates), content_type="application/json")
	
	data = {'dates': dates, 'events_maps': events_maps, 'events_timeline': events_timeline, 'percentiles': percentiles}
	return render_to_response('flatlab/admin/index.html', data, context_instance=RequestContext(request))
	