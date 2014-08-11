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
	
	# get referral code if exists
	inputs = request.GET if request.GET else None
	form = ReferralForm(inputs)
	referred_by = None
	if (inputs) and form.is_valid():
		cd = form.cleaned_data
		referred_by = cd['ref']
	
	inputs = request.POST if request.POST else None
	form = SplashForm(inputs)
	try:
		if (inputs) and form.is_valid():
			
			cd = form.cleaned_data
			
			# create user in Parse and check for parse errors
			created = create_parse_user(cd['email'], referred_by)
			if 'error'in created:
				raise Exception(created['error'])	
			
			return HttpResponseRedirect(reverse('confirmation-signup', kwargs={'ref': created['ref']}))
	
		else:
			raise Exception()

	except Exception as err:
		form.errors['__all__'] = form.error_class([err])
		return render_to_response('flatlab/admin/splash.html', {'form': form}, context_instance=RequestContext(request))

def eventsList(request, loc=None):
	
	inputs = request.POST if request.POST else None
	form = LocationForm(inputs)
		
	#if loc and loc not in locations.keys():	
	#	raise Http404
	
	if 'token' in request.session:	
		
		current_time = current_time_aware()

		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			
			# pull event listings and locations
			events , curDateTime = pullEvents(cd['lat'], cd['lng'], date=current_time)
			return HttpResponse(json.dumps((events, curDateTime)), content_type="application/json")
			comments = pull_recent_parse_comments_by_location(cd['lat'], cd['lng'], date=current_time)
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
			
			request.session['username'] = cd['username']
			request.session['token'] = token['token']
			request.session['ref'] = token['ref']
			
			return HttpResponseRedirect(reverse('eventsList'))
		else:
			raise Exception()
	
	except Exception as err:
		form.errors['__all__'] = form.error_class([err])
		data = {'form': form}
		return render_to_response('flatlab/admin/login.html', data, context_instance=RequestContext(request))
"""
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
"""
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
def updateEventsDB(request):
	
	current_time = datetime.datetime.now()
	locations = ['San Francisco', 'Oakland', 'Berkeley', 'Los Angeles']
	results = {}
	for i in locations:
		events = searchEventbrite(i, current_time)
		results[i] = events
	return HttpResponse(json.dumps(results), content_type="application/json")
	#return render_to_response('flatlab/admin/detail.html', data, context_instance=RequestContext(request))	
"""
def confirmation(request):	
	return render_to_response('flatlab/admin/confirmation.html', {'locations': locations}, context_instance=RequestContext(request))

def share(request):
	try:
		ref = request.session['ref']
		count = count_referrals(ref)
		return render_to_response('flatlab/admin/share.html', {'ref': ref, 'count': count}, context_instance=RequestContext(request))
	except:
		raise Http404
	
def confirmationSignup(request, ref):
	return render_to_response('flatlab/admin/confirmation-signup.html', {'ref': ref, 'count': 0}, context_instance=RequestContext(request))

def tos(request):
	data = {'locations': locations}
	return render_to_response('flatlab/admin/tos.html', data, context_instance=RequestContext(request))	

def confirmationEmail(request):
		
	inputs = request.GET if request.GET else None
	form = UserLogin(inputs)
	if (inputs) and form.is_valid():
		cd = form.cleaned_data
		email = cd['username']
		
		# credit referrer if applicable
		confirm_referral(email)
	
		# send welcome email to registered user
		send_welcome_email(email)
		
	return render_to_response('flatlab/admin/confirmation-email-static.html')

	


"""
API endpoint views
"""
def apiSignup(request):
	inputs = request.POST if request.POST else None
	form = ApiSignupForm(inputs)
	if (inputs) and form.is_valid():
			cd = form.cleaned_data
			resp = create_parse_user(cd['email'], cd['ref'])
			return HttpResponse(json.dumps(resp), content_type="application/json")
	else:
		return HttpResponse(json.dumps({'error': [(k, v[0]) for k, v in form.errors.items()]}), content_type="application/json")

def apiLogin(request):
	inputs = request.GET if request.GET else None
	form = ApiLoginForm(inputs)
	if (inputs) and form.is_valid():
			cd = form.cleaned_data
			resp = parse_login(cd['email'])
			return HttpResponse(json.dumps(resp), content_type="application/json")
	else:
		return HttpResponse(json.dumps({'error': [(k, v[0]) for k, v in form.errors.items()]}), content_type="application/json")

def apiReferrals(request):
	inputs = request.GET if request.GET else None
	form = ApiRefForm(inputs)
	if (inputs) and form.is_valid():
			cd = form.cleaned_data
			resp = count_referrals(cd['ref'])
			return HttpResponse(json.dumps({'count': resp}), content_type="application/json")
	else:
		return HttpResponse(json.dumps({'error': [(k, v[0]) for k, v in form.errors.items()]}), content_type="application/json")

def apiEventsList(request):

	inputs = request.GET if request.GET else None
	form = LocationForm(inputs)
	if (inputs) and form.is_valid():
			cd = form.cleaned_data

			current_time = current_time_aware()

			# pull event listings and locations
			events , curDateTime = pullEvents(cd['lat'], cd['lng'], date=current_time)
			comments = pull_recent_parse_comments_by_location(cd['lat'], cd['lng'], date=current_time)
			data = {'events': events, 'comments': comments}
			data['datetime'] = conv_to_js_date(current_time)
			return HttpResponse(json.dumps(data), content_type="application/json")
	else:
		return HttpResponse(json.dumps({'error': [(k, v[0]) for k, v in form.errors.items()]}), content_type="application/json")		
	
def apiEventsDetail(request, event_id):
	data = get_event_detail(event_id)
	if data:
		return HttpResponse(json.dumps(data), content_type="application/json")
	else:
		return HttpResponse(json.dumps({'error': 'No event with this ID'}), content_type="application/json")

def apiEventsPostComment(request, event_id):
	
	inputs = request.POST if request.POST else None
	form = ApiCommentForm(inputs)	
	
	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			


			try:
				event = get_parse_event_by_id(event_id)			
			except:
				raise Exception('No event with this ID')
			posted_message = post_parse_comment(cd['email'], cd['message'], event)
			return HttpResponse(json.dumps(True), content_type="application/json")	
		else:
			form_errors = [(k, v[0]) for k, v in form.errors.items()]
			raise Exception(form_errors)

	except Exception as err:

		return HttpResponse(json.dumps({'error': err.message}), content_type="application/json")

def apiHighrise(request):

	inputs = request.POST if request.POST else None
	form = ApiHighriseForm(inputs)	
	
	if (inputs) and form.is_valid():
		cd = form.cleaned_data
		highrise_id = create_highrise_account(cd['email'], tag=cd['tag'])
		return HttpResponse(json.dumps({'highrise-id': highrise_id}), content_type="application/json")
	else:
		return HttpResponse(json.dumps({'error': [(k, v[0]) for k, v in form.errors.items()]}), content_type="application/json")
