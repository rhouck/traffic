from parse_rest.user import User
from parse_rest.datatypes import Object, Date
from parse_rest.connection import ParseBatcher

from django.template.loader import render_to_string
from django.views.generic.base import TemplateView
from django.core.mail import send_mail
from django.utils.timezone import utc

import datetime
from dateutil.parser import parse
from dateutil import tz
import urllib2
import urllib
import json
import pprint
import pyrise
import time



from settings import EVENTBRITEKEYS, HIGHRISE_CONFIG, DEFAULT_FROM_EMAIL, LIVE

locations = {'SF': {'name': 'San Francisco', 'timezone': 'America/Los_Angeles'},
			 'BER': {'name': 'Berkeley', 'timezone': 'America/Los_Angeles'},
			 #'LA': {'name': 'Los Angeles', 'timezone': 'America/Los_Angeles'},
			 'OAK': {'name': 'Oakland', 'timezone': 'America/Los_Angeles'},
			 'SJ': {'name': 'San Jose', 'timezone': 'America/Los_Angeles'},
			 'PA': {'name': 'Palo Alto', 'timezone': 'America/Los_Angeles'},
			 'MV': {'name': 'Mountain View', 'timezone': 'America/Los_Angeles'},
			 }


class EmailList(Object):
    pass

class TestEvent(Object):
    pass

class LiveEvent(Object):
    pass

def get_event_type():
	if LIVE:
		return LiveEvent
	else:
		return TestEvent


class Comment(Object):
    pass

class TestComment(Object):
    pass

def post_parse_comment(user, message, event):
	if LIVE:
		comment = Comment(user=user, message=message, event=event, city=event.City, event_end_date=event.EndDate)
	else:
		comment = TestComment(user=user, message=message, event=event, city=event.City, event_end_date=event.EndDate)
	
	comment.save()
	return comment

class EventSizePercentile(Object):
    pass

def current_time_aware():
    return datetime.datetime.utcnow().replace(tzinfo=utc)

def conv_to_js_date(date):
    return 1000 * time.mktime(date.timetuple())

def get_local_datetime(location, cur_utc=current_time_aware(), locations=locations):
	for k, v in locations.iteritems():
		if v['name'] == location:
			timezone = tz.gettz(v['timezone'])
	
	date = cur_utc.astimezone(timezone)
	return date

	
def pull_parse_comments_by_event(event):
	
	if LIVE:
		comments = Comment.Query.all().filter(event=event)
	else:
		comments = TestComment.Query.all().filter(event=event)
	
	comments = comments.order_by("-createdAt")
	comments = comments.limit(100)
	comments = [c for c in comments]
	comments.reverse()
	return comments


def pull_recent_parse_comments_by_location(location):
	
	date = get_local_datetime(location)
	date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
	
	if LIVE:
		comments = Comment.Query.all().filter(city=location, event_end_date__gte=date)
	else:
		comments = TestComment.Query.all().filter(city=location, event_end_date__gte=date)
	
	comments = comments.order_by("-createdAt")
	comments = comments.limit(200)
	comments = [c for c in comments]
	return comments

def get_parse_user_by_username(username):
	user = User.Query.get(username=str(username))
	return user
	"""
	if not username:
		raise Exception("No username submitted")
	
	users = User.Query.all().filter(username=username)
	users = [u for u in users]
	
	if len(users) == 0:
		raise Exception("No users returned")
	elif len(users) > 1:
		raise Exception("Returned multiple users")
	else:
		return users[0]
	"""

def calc_percentile(bank, item):
	
	size = len(bank)
	if size == 0:
		return "--"
	else:
		point = size
		sorted_bank = sorted(bank)
		for ind, i in enumerate(bank):
			if item <= i:
				point = ind + 1
				break
		percentile = int((point * (100.0)) / size)
		return percentile

def get_parse_event_by_id(objectId):
	parse_event = get_event_type()
	event = parse_event.Query.get(objectId=str(objectId))
	return event

def pullEvents(location, date=current_time_aware()):
	
	date = get_local_datetime(location,cur_utc=date)

	# set date ranges
	date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
	beg_date = date - datetime.timedelta(days=0)
	end_date = date + datetime.timedelta(days=6)
	parse_beg_date = Date(beg_date)
	parse_end_date = Date(end_date)

	# run Parse query
	#events = TestEvent.Query.all().filter(City=location, StartDate__gte=parse_beg_date, EndDate__lte=parse_end_date, Lat__gte=-10000000, Lng__gte=-100000000)
	parse_event = get_event_type()
	events = parse_event.Query.all().filter(City=location, StartDate__lte=parse_end_date, EndDate__gte=parse_beg_date, Lat__gte=-10000000, Lng__gte=-100000000)
	events = events.order_by("EndTime")
	events = events.limit(500)
	events = [e for e in events if (e.Address)]
	
	
	# split into individual days
	events_split = {}
	for i in range((end_date-beg_date).days):
		date = beg_date + datetime.timedelta(days=i)
		events_split[date.date()] = []

		# add item to sub list if is live during the day question
		# index for timeline formatting
		index = 1
		for k in events:
			
			k.Capacity = int(k.Capacity) if k.Capacity else None

			if k.StartDate >= date and k.EndDate <= date:
				
				# set index for timeline formatting
				k.index  = index
				index += 1
				if index > 4:
					index = 1

				# format EndTime
				pretty_EndTime = parse(k.EndTime).strftime("%I:%M %p")
				k.pretty_EndTime = pretty_EndTime
				if pretty_EndTime[0] == "0":
					pretty_EndTime = pretty_EndTime[1:]
				pretty_StartTime = parse(k.StartTime).strftime("%I:%M %p")
				if pretty_StartTime[0] == "0":
					pretty_StartTime = pretty_StartTime[1:] 
				#k.pretty_full_Time = "%s - %s" % (pretty_StartTime, pretty_EndTime)
				k.pretty_StartTime = pretty_StartTime
				k.pretty_EndTime = pretty_EndTime
				k.pretty_full_Time = "%s - %s" % (pretty_StartTime, pretty_EndTime)
				
				# string for ajax
				k.ajax_string = json.dumps({'name': k.Name, 'objectId': k.objectId, 'Lat':k.Lat, 'Lng': k.Lng})

				# add item to events list
				events_split[date.date()].append(k)
	
	sorted_keys = sorted(events_split.keys())
	
	capacities_query = EventSizePercentile.Query.all().filter(City=location)
	capacities_query = capacities_query.order_by("createdAt").limit(1)
	
	for c in capacities_query:
		capacities = c
	
	# turn dic into sorted list for easy iteration on client side
	events_sorted = []
	caps = []
	for i in sorted_keys:
		for k in events_split.iterkeys():
			if i == k:
				temp = [{'tag': "PPL: %s\nEnding: %s" % (t.Capacity, t.pretty_EndTime), 'lat': t.Lat, 'lng': t.Lng} for t in events_split[k]]
				events_sorted.append(temp)
				cap = sum([t.Capacity for t in events_split[k]])
				caps.append(cap)
				#percentiles.append(percentileofscore(capacities.Capacities, cap))
				#percentiles.append(calc_percentile(capacities.Capacities, cap))
	
	# select category from percentiles
	categories = []
	for i in caps:
		"""
		percentile = calc_percentile(caps, i)
		category = 1
		if percentile >= 25:
			category = 2
		elif percentile >= 75:
			category = 3
		categories.append(category)
		"""
		categories.append(2)

	#combine percentiles/categories and dates
	dates = []
	for ind, i in enumerate(sorted_keys):
		dates.append([i, categories[ind]])

	return (dates, events_sorted, events_split)	

def searchEventbrite(location, date):
	
	date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
	beg_date = date - datetime.timedelta(days=0)
	end_date = date + datetime.timedelta(days=6)
	
	# run Parse query
	parse_event = get_event_type()
	events = parse_event.Query.all().filter(City=location)
	events = events.order_by("createdAt")
	events = events.limit(1)
	events = [e for e in events]
	if events:
		last_update = events[0].createdAt
	else:
		last_update = None
	"""
	eb_auth_tokens = {'app_key':  EVENTBRITEKEYS['app_key'],
					  'access_code': EVENTBRITEKEYS['access_code']}
	eb_client = eventbrite.EventbriteClient(eb_auth_tokens)
	
	event_search = eb_client.event_search({'city': location, 'start_date.range_start': beg_date, 'start_date.range_end': end_date})
	"""
	params =   {'token': EVENTBRITEKEYS['access_code'],
				'venue.city': location,
				'start_date.range_start': '%s-%s-%sT00:00:00Z' % (beg_date.year, beg_date.month, beg_date.day),
				'start_date.range_end': '%s-%s-%sT00:00:00Z' % (end_date.year, end_date.month, end_date.day),
				}
			

	try:
		event_search = sendRequest('https://www.eventbriteapi.com/v3/events/search', data=params)
		if not event_search['success']:
			raise Exception("Error searching EventBrite for %s - %s" % (location, event_search['error']))
		
		results = []
		for event in event_search['response']['events']:
			results.append(event)
		
		total_pages = event_search['response']['pagination']['page_count']
		
		if total_pages > 1:
			for p in range(2, total_pages+1):
				# rerun search on next page
				params['page'] = p
				event_search = sendRequest('https://www.eventbriteapi.com/v3/events/search', data=params)
				if not event_search['success']:
					raise Exception("Error searching EventBrite for %s" % (location))
				for event in event_search['response']['events']:
					results.append(event)
				

		# get address data
		for i in results:
			venue_search = sendRequest(i['venue']['resource_uri'], data={'token': EVENTBRITEKEYS['access_code'],})
			if not venue_search['success']:
				raise Exception("Error searching EventBrite for %s" % (location))
			i['venue'] = venue_search['response']


		# save event data into parse
		batcher = ParseBatcher()
		items = []
		index = 1
		
		for i in results:
		
			if index == 50:
				try:		
					batcher.batch_save(items)
				except Exception as err:
					raise Exception("Error saving to Parse for %s - %s" % (location,err))
				
				items = []
				index = 1
			
			entry = Event()	
				
			entry.Name = i['name']['text']
			
			entry.Address = "" 
			if i['venue']['address_1']:
				  entry.Address += i['venue']['address_1']
			if i['venue']['address_2']:
				  entry.Address += " %s" % (i['venue']['address_2'])
			entry.City = location
			entry.Country = "United States"
			entry.Lat = i['venue']['latitude']
			entry.Lng = i['venue']['longitude']

			entry.Capacity = int(i['capacity'])

			entry.Timezone = i['start']['timezone']
			dt = i['start']['local'].split("T")
			d = dt[0].split("-")
			entry.StartTime = dt[1]
			entry.StartDay = int(d[2])
			entry.StartMonth = int(d[1])
			entry.StartYear = int(d[0])
			dt = i['end']['local'].split("T")
			d = dt[0].split("-")
			entry.EndTime = dt[1]
			entry.EndDay = int(d[2])
			entry.MonthEnd = int(d[1])
			entry.YearEnd = int(d[0])

			entry.StartDate = Date(datetime.datetime(entry.StartYear, entry.StartMonth, entry.StartDay,0,0,0))
			entry.EndDate = Date(datetime.datetime(entry.YearEnd, entry.MonthEnd, entry.EndDay,0,0,0))
			
			items.append(entry)
			index += 1
			
		if items:
			try:		
				batcher.batch_save(items)
			except Exception as err:
				raise Exception("Error saving to Parse for %s - %s" % (location,err))

		return True 
		
	except Exception as err:
		return err
	

def daily_event_size(location):
	
	# this determines typical size and number of events in an area to determine if a date is relatively busy or slow
	# to-do: update to only consider historical and most recently acquired data

	# run Parse query
	date = datetime.datetime.now()
	date = Date(datetime.datetime(date.year, date.month, date.day, 0, 0, 0))
	parse_event = get_event_type()
	events_query = parse_event.Query.all().filter(StartDate__lte=date)
	events_query = events_query.limit(5000)
	events = []
	for e in events_query:
		events.append(e)
	
	min_date = None
	min_event = None
	max_date = None
	max_event = None
	for i in events:
		if not min_date or i.StartDate < min_date:
			min_date = i.StartDate
			min_event = i
		if not max_date or i.EndDate > max_date:
			max_date = i.EndDate
			max_event = i

	date_range = (max_date-min_date).days

	capacities = {}
	for i in range(date_range):
		date = min_date + datetime.timedelta(days=i)
		for e in events:		
			event_length = (e.EndDate-e.StartDate).days
			
			# filter out long-running or perpetual events
			if e.StartDate <= date and e.EndDate >= date and event_length <= 14:
				if date not in capacities:
					capacities[date] = []
				capacities[date].append(e.Capacity)
	
	# remove small sets
	small_sets = []
	for k, v in capacities.iteritems():
		if len(v) < 5:
			small_sets.append(k)
	for i in small_sets:
		del capacities[i]

	# sum the sizes of each event
	for k,v in capacities.iteritems():
		capacities[k] = sum(v)

	# build list of capacities
	capacities_list = []
	for k,v in capacities.iteritems():
		capacities_list.append(v)
	
	entry = EventSizePercentile()
	entry.City = location
	entry.Capacities = capacities_list
	entry.save()

	return capacities


def sendRequest(url, data={}, headers=None, method='get'):

  try:

    url_values = urllib.urlencode(data)

    if method == 'get':
      url = url + '?' + url_values
      data = urllib2.urlopen(url)

    elif method == 'post':

      if headers:
        if headers['Content-Type'] == 'application/json':
          if 'query_params' in data:
            url_values = urllib.urlencode(data['query_params'])
            url = url + '?' + url_values
            del data['query_params']
          url_values = json.dumps(data)
        req = urllib2.Request(url, url_values, headers)
      else:
        req = urllib2.Request(url, url_values)

      data = urllib2.urlopen(req)

    else:
      raise Exception("Impropper method: '%s'" % method)

    return {'success': True, 'response': json.loads(data.read())}

  except urllib2.HTTPError as e:
    return {'success': False, 'error': "The server couldn't fulfill the request: %s - %s" % (e.code, e.reason)}
  except urllib2.URLError as e:
    return {'success': False, 'error': "We failed to reach a server: %s" % (e.reason)}
  except Exception as err:
    return {'success': False, 'error': str(err)}


"""
class AjaxView(TemplateView):
  def render_to_json(self, data):
    return HttpResponse(json.dumps(data), content_type='application/json')

class AjaxOnlyView(AjaxView):
  def dispatch(self, *args, **kwargs):
    if not self.request.is_ajax():
      return permission_denied(self.request)

    return super(AjaxView, self).dispatch(*args, **kwargs)
"""


def create_highrise_account(user, tag=None):
	
	pyrise.Highrise.set_server(HIGHRISE_CONFIG['server'])
	pyrise.Highrise.auth(HIGHRISE_CONFIG['auth'])

	if not user.highrise_id:
		try:

			cust = pyrise.Person()

			cust.contact_data = pyrise.ContactData(email_addresses=[pyrise.EmailAddress(address=user.email, location='Home'),],)

			cust.first_name = user.username

			cust.save()
			cust.add_tag('DriversWanted')
			if tag:
				cust.add_tag(tag)

			user.highrise_id = cust.id

		except:
		    pass
	else:
		if tag:
			try:
				cust = pyrise.Person.get(user.highrise_id)
				cust.add_tag(tag)
			except:
				pass

def create_highrise_and_tag(email, tag):
	try:
		# check if user exists and add to highrise if does not
		class TempUser(object):
			pass
		user = TempUser()
		user.highrise_id = None
		user.email = email
		user.username = email
		create_highrise_account(user, tag)
	except:
		pass	


def send_email(to_email, subject, body):

	send_mail(subject, body, DEFAULT_FROM_EMAIL,[to_email], fail_silently=False)
	return True
