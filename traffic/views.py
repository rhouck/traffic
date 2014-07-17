from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib.auth.views import logout
from django.contrib.auth.views import login
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.forms.util import ErrorList

import datetime
import json
import ast

from utils import *
from forms import *

from parse_rest.user import User


def splash(request):
	return render_to_response('flatlab/admin/splash.html', {'locations': locations}, context_instance=RequestContext(request))


def eventsList(request, loc=None):
	
	#return HttpResponse(json.dumps(loc), content_type="application/json")
	if loc and loc not in locations.keys():	
		raise Http404
	
	elif loc and 'username' in request.session:		
		request.session['city'] = loc
		current_time = datetime.datetime.now()
		dates, events_maps, events_timeline = pullEvents(locations[loc], current_time)
		#return HttpResponse(json.dumps(percentiles), content_type="application/json")
		
		data = {'dates': dates, 'events_maps': events_maps, 'events_timeline': events_timeline, 'locations': locations, 'selected': loc}
		return render_to_response('flatlab/admin/main.html', data, context_instance=RequestContext(request))	
	else:
		return HttpResponseRedirect(reverse('splash'))
		

def logout(request):
	
	# save final city view
	if 'city' in request.session:
		user = User.login(request.session['username'], request.session['password'])
		user.CityPref = request.session['city']
		user.save()
	
	request.session.flush()
	return HttpResponseRedirect(reverse('splash'))


def login(request):
	
	inputs = request.POST if request.POST else None
	form = UserLogin(inputs)

	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			
			# log user in if successful
			try:
				user = User.login(cd['username'], cd['password'])
			except Exception as err:
				form.errors['__all__'] = form.error_class([ast.literal_eval(err[0])['error']])
				raise Exception()		

			# set session vars
			request.session['username'] = cd['username']
			request.session['password'] = cd['password']
			
			return HttpResponseRedirect(reverse('eventsList', kwargs={'loc': user.CityPref}))
		else:
			raise Exception()
	except Exception as err:
		#return HttpResponse(json.dumps(str(err)), content_type="application/json")
		data = {'form': form, 'locations': locations}
		return render_to_response('flatlab/admin/login.html', data, context_instance=RequestContext(request))

def signup(request):

	inputs = request.POST if request.POST else None
	form = UserSignup(inputs)
	
	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			
			# password check	
			if cd['password'] != cd['password2']:
				errors = form._errors.setdefault("password", ErrorList())
				errors.append(u"Password do not match")
				raise Exception()	
			
			# create user in Parse and check for parse errors
			try:
				user = User.signup(cd['username'], cd['password'], email=cd['email'], CityPref="SF", company=cd['company'], highrise_id=None)
			except Exception as err:
				form.errors['__all__'] = form.error_class([ast.literal_eval(err[0])['error']])
				raise Exception()
			
			# log user in if successful
			try:
				user = User.login(cd['username'], cd['password'])
				
				user.save()
			except Exception as err:
				form.errors['__all__'] = form.error_class([ast.literal_eval(err[0])['error']])
				raise Exception()	
			
			# add to highrise
			create_highrise_account(user, 'user')
			user.save()
			
			# set session vars
			request.session['username'] = cd['username']
			request.session['password'] = cd['password']
			
			return HttpResponseRedirect(reverse('eventsList', kwargs={'loc': user.CityPref}))
		else:
			raise Exception()
	except Exception as err:
		#return HttpResponse(json.dumps(str(err)), content_type="application/json")
		
		data = {'form': form, 'locations': locations}
		return render_to_response('flatlab/admin/signup.html', data, context_instance=RequestContext(request))

def tos(request):
	data = {'locations': locations}
	return render_to_response('flatlab/admin/tos.html', data, context_instance=RequestContext(request))	


def eventDetail(request):
	data = []
	return render_to_response('flatlab/admin/detail.html', data, context_instance=RequestContext(request))	

def contact(request):
	inputs = request.POST if request.POST else None
	form = ContactForm(inputs)
	
	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			
			# check if user exists and add to highrise if does not
			class TempUser(object):
				pass
			user = TempUser()
			user.highrise_id = None
			user.email = cd['email']
			user.username = cd['email']
			create_highrise_account(user, 'contact')
			
			send_email('info.driverswanted@gmail.com', 'Contact Form', cd['message'])

			if 'city' in request.session: 
				loc = request.session['city']
				return HttpResponseRedirect(reverse('eventsList', kwargs={'loc': request.session['city']}))
			else:
				return HttpResponseRedirect(reverse('splash'))		
			
		else:
			raise Exception()
	
	except Exception as err:
		data = {'form': form, 'locations': locations, 'error': str(err)}
		return render_to_response('flatlab/admin/contact.html', data, context_instance=RequestContext(request))

	



"""
class MyView(AjaxOnlyView):
  def get(self, *args, **kwargs):
    return self.render_to_json({'success':True,html:render_to_string('ajax/includes/template.html',{'context':blah,'data':blah,'here':blah})})
"""

def updateEventsDB(request):
	
	current_time = datetime.datetime.now()
	locations = ['San Francisco', 'Oakland', 'Berkeley', 'Los Angeles']
	results = {}
	for i in locations:
		events = searchEventbrite(i, current_time)
		results[i] = events
	return HttpResponse(json.dumps(results), content_type="application/json")
	#return render_to_response('flatlab/admin/detail.html', data, context_instance=RequestContext(request))	
	