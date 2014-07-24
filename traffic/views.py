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
from dateutil.parser import parse

from utils import *
from forms import *
from settings import LIVE

from parse_rest.user import User

def splash(request):
	
	inputs = request.POST if request.POST else None
	form = SplashForm(inputs)
	try:
		if (inputs) and form.is_valid():
			
			cd = form.cleaned_data
			"""
			email_type = "live" if LIVE else 'test'
			new_email = EmailList(email=cd['email'], type=email_type)
			new_email.save()
			"""
			
			# create user in Parse and check for parse errors
			try:
				if LIVE:
					user = User.signup(cd['email'], "pass", email=cd['email'], CityPref="SF", type="live")
				else:
					user = User.signup(cd['email'], "pass", email=cd['email'], CityPref="SF", type="test")	
			except Exception as err:
				raise Exception(ast.literal_eval(err[0])['error'])
			
			if LIVE:
				create_highrise_and_tag(cd['email'], 'user')
			
			request.session['username'] = cd['email']
			return HttpResponseRedirect(reverse('eventsList', kwargs={'loc': "SF"}))
	
		else:
			raise Exception()

	except Exception as err:
		form.errors['__all__'] = form.error_class([err])
		return render_to_response('flatlab/admin/splash.html', {'locations': locations, 'form': form}, context_instance=RequestContext(request))

def eventsList(request, loc=None):
	
	
	if loc and loc not in locations.keys():	
		raise Http404
	
	elif loc and 'username' in request.session:	
		
		# set session variable
		request.session['city'] = loc
		# pull event listings and locations
		dates, events_maps, events_timeline = pullEvents(locations[loc]['name'])
		
		# pull recent comments
		binned_comments = {}
		for i in dates:
			binned_comments[i[0]] = []	
		total_comments = pull_recent_parse_comments_by_location(locations[loc]['name'])
		
		for i in total_comments:
			i.js_time = conv_to_js_date(i.createdAt)
			for k in binned_comments.iterkeys():
				date = datetime.datetime(k.year, k.month, k.day, 0, 0, 0)
				if i.event.StartDate >= date and i.event.EndDate <= date:
					binned_comments[k].append(i)
		
		data = {'dates': dates, 'events_maps': events_maps, 'events_timeline': events_timeline, 
				'locations': locations, 'selected': locations[loc]['name'], 'comments': binned_comments}
		return render_to_response('flatlab/admin/main.html', data, context_instance=RequestContext(request))	
	else:
		return HttpResponseRedirect(reverse('splash'))

def logout(request):
	
	# save final city view
	if 'city' in request.session:
		try:
			user = User.login(request.session['username'], "pass")
			user.CityPref = request.session['city']
			user.save()
		except:
			pass
	request.session.flush()
	return HttpResponseRedirect(reverse('splash'))


def login(request):
	
	inputs = request.POST if request.POST else None
	form = UserLogin(inputs)
		
	try:
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			
			try:
				user = get_parse_user_by_email(cd['username'])
			except Exception as err:
				raise Exception("Email not registered in system.")
			
			"""
			# log user in if successful
			try:
				user = User.login(cd['username'], "pass")
			except Exception as err:
				raise Exception(ast.literal_eval(err[0])['error'])		
			"""
			# set session vars
			request.session['username'] = user.email
			
			return HttpResponseRedirect(reverse('eventsList', kwargs={'loc': user.CityPref}))
		else:
			raise Exception()
	
	except Exception as err:
		form.errors['__all__'] = form.error_class([err])
		data = {'form': form, 'locations': locations}
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


def eventDetail(request, id):
	
	try:
		event = get_parse_event_by_id(id)
	except:
		raise Http404

	if 'username' in request.session:		

		data = {'locations': locations}
		#format event object
		pretty_EndTime = parse(event.EndTime).strftime("%I:%M %p")
		event.pretty_EndTime = pretty_EndTime
		if pretty_EndTime[0] == "0":
			pretty_EndTime = pretty_EndTime[1:]
		pretty_StartTime = parse(event.StartTime).strftime("%I:%M %p")
		if pretty_StartTime[0] == "0":
			pretty_StartTime = pretty_StartTime[1:] 

		event.pretty_StartTime = pretty_StartTime
		event.pretty_EndTime = pretty_EndTime

		map_data = [{'tag': "PPL: %s\nEnding: %s" % (t.Capacity, t.pretty_EndTime), 'lat': t.Lat, 'lng': t.Lng} for t in [event,]]
		

		# update comments if provided
		inputs = request.POST if request.POST else None
		form = CommentForm(inputs)	
		if (inputs) and form.is_valid():
			cd = form.cleaned_data
			# post comment
			posted_message = post_parse_comment(request.session['username'], cd['message'], event)
			
		# clear comment form
		form = CommentForm(None)
		
		# pull comments
		comments = pull_parse_comments_by_event(event)
		for c in comments:
			pretty_time = c.createdAt.strftime("%I:%M %p")
			short_date = c.createdAt.strftime("%b %d")
			if pretty_time[0] == "0":
				pretty_time = pretty_time[1:]	
			c.pretty_time = "%s, %s" % (short_date, pretty_time)
			c.js_time = conv_to_js_date(c.createdAt)

		data['comments'] = comments
		data['form']= form 
		data['events_map'] = map_data
		data['event'] = event.__dict__
		data['selected'] = locations[request.session['city']]['name']
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

def confirmation(request):	
	return render_to_response('flatlab/admin/confirmation.html', {'locations': locations}, context_instance=RequestContext(request))
def confirmationEmailList(request):
	return render_to_response('flatlab/admin/confirmation-email-list.html', {'locations': locations}, context_instance=RequestContext(request))
def tos(request):
	data = {'locations': locations}
	return render_to_response('flatlab/admin/tos.html', data, context_instance=RequestContext(request))	


	