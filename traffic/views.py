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
from dateutil.parser import parse

from utils import *
from forms import *
from settings import LIVE

from parse_rest.user import User

import random

def splash(request):
	
	inputs = request.POST if request.POST else None
	form = SplashForm(inputs)
	try:
		if (inputs) and form.is_valid():
			
			cd = form.cleaned_data
			
			# create user in Parse and check for parse errors
			created = create_parse_user(cd['email'])
			if 'error'in created:
				raise Exception(created['error'])	
			
			return HttpResponseRedirect(reverse('confirmation-signup', kwargs={'promo': created['promo']}))
	
		else:
			raise Exception()

	except Exception as err:
		form.errors['__all__'] = form.error_class([err])
		return render_to_response('flatlab/admin/splash.html', {'form': form}, context_instance=RequestContext(request))

def eventsList(request, loc=None):
	
	inputs = request.POST if request.POST else None
	form = LocationForm(inputs)
	#return HttpResponse(json.dumps(inputs), content_type="application/json")
		
	#if loc and loc not in locations.keys():	
	#	raise Http404
	
	if 'token' in request.session:	
		
		current_time = current_time_aware()

		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			

			# pull event listings and locations
			events , curDateTime = pullEvents(cd['lat'], cd['lng'], date=current_time)
			
			comments = pull_recent_parse_comments_by_location(cd['lat'], cd['lng'], date=current_time)
			#return HttpResponse(json.dumps(comments), content_type="application/json")
			data = {'events': events, 'comments': comments, 'show_events': True,}
		
		else:
			data = {'datetime': None, 'events': [], 'comments': [],}
		
		data['datetime'] = conv_to_js_date(current_time)
		data['form'] = form
		#data['locations'] = locations
		#data['selected'] = locations[loc]['name']
		return render_to_response('flatlab/admin/main.html', data, context_instance=RequestContext(request))	
	else:
		return HttpResponseRedirect(reverse('splash'))

def logout(request):
	
	# save final city view
	request.session.flush()
	return HttpResponseRedirect(reverse('splash'))


def login(request):
	
	inputs = request.POST if request.POST else None
	form = UserLogin(inputs)
		
	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
				
			token = parse_login(cd['username'])
			if 'error' in token:
				raise Exception(token['error'])
			request.session['token'] = token['token']
			
			return HttpResponseRedirect(reverse('eventsList'))
		else:
			raise Exception()
	
	except Exception as err:
		form.errors['__all__'] = form.error_class([err])
		data = {'form': form}
		return render_to_response('flatlab/admin/login.html', data, context_instance=RequestContext(request))

def signup(request):

	inputs = request.POST if request.POST else None
	if inputs:
		form = UserSignup(inputs)
	else:
		form = UserSignup(initial={'location': 'SF'})
	
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
				if LIVE:
					user = User.signup(cd['username'], cd['password'], email=cd['email'], phone=cd['phone'], CityPref=cd['location'], company=cd['company'], highrise_id=None, type="live")
				else:
					user = User.signup(cd['username'], cd['password'], email=cd['email'], phone=cd['phone'], CityPref=cd['location'], company=cd['company'], highrise_id=None, type="test")
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
			if LIVE:
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


def eventDetail(request, event_id):
	
	
	
	if 'token' in request.session:		

		# update comments if provided
		inputs = request.POST if request.POST else None
		form = CommentForm(inputs)	
		
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			# post comment
			event = get_parse_event_by_id(event_id)
			posted_message = post_parse_comment(request.session['username'], cd['message'], event)
			return HttpResponseRedirect(reverse('event-detail', kwargs={'event_id': event_id}))	
		
		else:
		
			data = get_event_detail(event_id)
			data['form']= form 
			return render_to_response('flatlab/admin/detail.html', data, context_instance=RequestContext(request))	

	else:
		return HttpResponseRedirect(reverse('splash'))


def contact(request):
	inputs = request.POST if request.POST else None
	form = ContactForm(inputs)
	
	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			
			if LIVE:
				create_highrise_and_tag(cd['email'], 'contact')

			message = "From %s:\n\n%s" % (cd['email'], cd['message'])
			send_email('info.driverswanted@gmail.com', 'Contact Form', message)
			"""
			if 'city' in request.session: 
				loc = request.session['city']
				return HttpResponseRedirect(reverse('eventsList', kwargs={'loc': request.session['city']}))
			else:
				return HttpResponseRedirect(reverse('confirmation'))		
			"""
			return HttpResponseRedirect(reverse('confirmation'))
		else:
			raise Exception()
	
	except Exception as err:
		data = {'form': form, 'error': str(err)}
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

def confirmation(request):	
	return render_to_response('flatlab/admin/confirmation.html', {'locations': locations}, context_instance=RequestContext(request))
def confirmationSignup(request, promo):
	return render_to_response('flatlab/admin/confirmation-signup.html', {'promo': promo}, context_instance=RequestContext(request))
def tos(request):
	data = {'locations': locations}
	return render_to_response('flatlab/admin/tos.html', data, context_instance=RequestContext(request))	
def confirmationEmail(request):
	return render_to_response('flatlab/admin/confirmation-email-static.html')

	