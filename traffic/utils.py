from parse_rest.user import User
from parse_rest.datatypes import Object, Date, GeoPoint
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
from math import radians, cos, sin, asin, sqrt
from random import choice
import string
import ast

from settings import EVENTBRITEKEYS, HIGHRISE_CONFIG, DEFAULT_FROM_EMAIL, LIVE, BASE


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    m = km * 0.621371
    return m



locations = {'SF': {'name': 'San Francisco', 'timezone': 'America/Los_Angeles'},
			 'BER': {'name': 'Berkeley', 'timezone': 'America/Los_Angeles'},
			 #'LA': {'name': 'Los Angeles', 'timezone': 'America/Los_Angeles'},
			 'OAK': {'name': 'Oakland', 'timezone': 'America/Los_Angeles'},
			 'SJ': {'name': 'San Jose', 'timezone': 'America/Los_Angeles'},
			 'PA': {'name': 'Palo Alto', 'timezone': 'America/Los_Angeles'},
			 'MV': {'name': 'Mountain View', 'timezone': 'America/Los_Angeles'},
			 }


def parse_login(email):	
	
	try:
		user = get_parse_user_by_email(email)
	except:
		return {'error': "No one has signed up with this address."}
		
	if not user.emailVerified:
		return {'error': "Email address not verified. Plase check inbox."}

	u = User.login(email, "pass")
	header = u.session_header()
	return {'token': header['X-Parse-Session-Token']}


class Referrals(Object):
    pass

def create_parse_user(email, referred_by=None):
	try:
		if LIVE:
			user_type = "live"
		else:
			user_type = "test"
		ref = gen_alphanum_key()
		user = User.signup(email, "pass", email=email, type=user_type, ref=ref)	
	except Exception as err:
		return {'error': ast.literal_eval(err[0])['error']}

	if LIVE:
		highrise_id = create_highrise_account(email, 'user')
		user.highrise_id = highrise_id
		user.save()

	if referred_by:
		referral = Referrals(user=user, email=email, code=referred_by, verified=False)
		referral.save()

	return {'created': True, 'ref': ref}

def confirm_referral(email):
	
	# check if this email address was referred
	ref = Referrals.Query.all().filter(email=email, verified=False)
	ref = [r for r in ref]
	
	if len(ref) > 0:
		# check if theres a user tied to the associated referral code
		ref = ref[0]
		referrer = User.Query.all().filter(ref=ref.code)
		referrer = [r for r in referrer]
		
		if len(referrer) > 0:
			# updated verified status of referral
			referrer = referrer[0]
			ref.verified = True
			ref.save()
			
			# send email to referrer
			ref = Referrals.Query.all().filter(code=ref.code, verified=True)
			count = len([r for r in ref])
			
			subject = "Almost There | CabTools Free for 6 Months"

			send_email(referrer.email, subject, str(count))
			
	
	
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


def gen_alphanum_key():
    key = ''
    for i in range(8):
        key += choice(string.uppercase + string.lowercase + string.digits)
    return key

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
	comments = comments.limit(50)
	
	formatted_comments = []
	for c in comments:
		pretty_time = c.createdAt.strftime("%I:%M %p")
		short_date = c.createdAt.strftime("%b %d")
		if pretty_time[0] == "0":
			pretty_time = pretty_time[1:]	
		c.pretty_time = "%s, %s" % (short_date, pretty_time)
		c.js_time = conv_to_js_date(c.createdAt)
		
		entry = c.__dict__
		del entry['user']
		del entry['_updated_at']
		del entry['event_end_date']
		del entry['_created_at']
		del entry['event']
		del entry['objectId']
		del entry['city']
		formatted_comments.append(entry)


	formatted_comments.reverse()
	return formatted_comments


def pull_recent_parse_comments_by_location(lat, lng, date=current_time_aware(), max_dist=5):
	
	# set current location
	cur_loc = GeoPoint(latitude=float(lat), longitude=float(lng))

	# set date ranges
	beg_date = date - datetime.timedelta(hours=1)
	end_date = date + datetime.timedelta(hours=5)
	parse_beg_date = Date(beg_date)
	parse_end_date = Date(end_date)
	
	if LIVE:
		comments = Comment.Query.all()
	else:
		comments = TestComment.Query.all()

	
	#comments = comments.filter(event_location__nearSphere=cur_loc)
	comments = comments.order_by("-createdAt")
	comments = comments.limit(50)
	
	filtered = []
	for c in comments:
		c.distance = haversine(cur_loc.longitude, cur_loc.latitude, c.event.location.longitude, c.event.location.latitude)
		if c.distance > max_dist:
			break
		
		c.js_time = conv_to_js_date(c.createdAt)
		
		entry = c.__dict__
		del entry['_created_at']
		del entry['_updated_at']
		del entry['objectId']
		del entry['event_end_date']
		entry['event_id'] = entry['event'].objectId
		entry['event_title'] = "%s miles - %s" %(("%.2f" % c.distance), entry['event'].Address)
		del entry['event']
		
		filtered.append(entry)

	return filtered

def get_parse_user_by_username(username):
	user = User.Query.get(username=str(username))
	return user

def get_parse_user_by_email(email):
	user = User.Query.get(email=str(email))
	return user

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

def pullEvents(lat, lng, date=current_time_aware(), max_dist=5):
	
	# temporary (remove once done testing)
	#date = date - datetime.timedelta(days=5)

	# set current location
	cur_loc = GeoPoint(latitude=float(lat), longitude=float(lng))

	# set date ranges
	beg_date = date - datetime.timedelta(hours=1)
	end_date = date + datetime.timedelta(hours=5)
	parse_beg_date = Date(beg_date)
	parse_end_date = Date(end_date)

	# run Parse query
	parse_event = get_event_type()
	#events = parse_event.Query.all().filter(StartDate__lte=parse_end_date, EndDate__gte=parse_beg_date, Lat__gte=-10000000, Lng__gte=-100000000)
	events = parse_event.Query.filter(location__nearSphere=cur_loc)
	#events = events.order_by("EndTime")
	events = events.limit(50)
	events = [e for e in events if (e.Address)]
	
	"""
	# split into individual days
	events_split = {}
	for i in range((end_date-beg_date).days):
		date = beg_date + datetime.timedelta(days=i)
		events_split[date.date()] = []
	"""
	# add item to sub list if is live during the day question
	# index for timeline formatting
	formatted_events = []
	index = 1
	for k in events:
		
		# calcualte distance from user
		k.distance = haversine(cur_loc.longitude, cur_loc.latitude, k.location.longitude, k.location.latitude)
		# break once next closest event is further than max_dist
		if k.distance > max_dist:
			break
		k.distance = ("%.2f" % k.distance)
		k.Capacity = int(k.Capacity) if k.Capacity else None
			
		# set index for timeline formatting
		k.index  = index
		index += 1
		if index > 4:
			index = 1

		# format EndTime
		pretty_EndTime = parse(k.EndTime).strftime("%I:%M %p")
		if pretty_EndTime[0] == "0":
			pretty_EndTime = pretty_EndTime[1:]
		
		pretty_StartTime = parse(k.StartTime).strftime("%I:%M %p")
		if pretty_StartTime[0] == "0":
			pretty_StartTime = pretty_StartTime[1:] 
	
		k.pretty_StartTime = pretty_StartTime
		k.pretty_EndTime = pretty_EndTime
		k.pretty_full_Time = "%s - %s" % (pretty_StartTime, pretty_EndTime)
		
		k.StartDate = str(k.StartDate)
		k.EndDate = str(k.EndDate)
		
		k.tag = "PPL: %s\nEnding: %s" % (k.Capacity, k.pretty_EndTime)
		k.id = k.objectId		
		
		# add item to events list
		entry = k.__dict__
		del entry['_created_at']
		del entry['_updated_at']
		#del entry['_object_id']
		del entry['objectId']
		del entry['location']

		# remove unicode types
		for k, v in entry.iteritems():
			if isinstance(v, unicode): 
				entry[k] = str(v)

		formatted_events.append(entry)
	
	return (formatted_events, conv_to_js_date(date))


def get_event_detail(id):
	
	try:
		event = get_parse_event_by_id(id)

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

		# set map data
		map_data = [{'tag': str("%s\nEnding: %s" % (t.Name, t.pretty_EndTime)), 'lat': t.Lat, 'lng': t.Lng} for t in [event,]]
		
		# pull comments
		comments = pull_parse_comments_by_event(event)
		
		data = {}
		data['comments'] = comments
		data['events_map'] = map_data
		

		event = event.__dict__
			
		del event['_created_at']
		del event['_updated_at']
		#del event['_object_id']
		del event['objectId']
		del event['location']
		
		# change date format type
		event['StartDate'] = conv_to_js_date(event['StartDate'])
		event['EndDate'] = conv_to_js_date(event['EndDate'])

		# remove unicode and date types
		for k, v in event.iteritems():
			if isinstance(v, (unicode)): 
				event[k] = str(v)
		
		data['event'] = event
		
		return data
		
	except Exception as err:
		
		return str(err)
		


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

def create_highrise_account(email, tag=None):
	
	pyrise.Highrise.set_server(HIGHRISE_CONFIG['server'])
	pyrise.Highrise.auth(HIGHRISE_CONFIG['auth'])

	try:

		cust = pyrise.Person()

		cust.contact_data = pyrise.ContactData(email_addresses=[pyrise.EmailAddress(address=email, location='Home'),],)

		cust.first_name = email

		cust.save()
		
		cust.add_tag('CabTools')
		if tag:
			cust.add_tag(tag)

		return cust.id
		
	except:
	    
	    return None

def send_email(to_email, subject, body):

	send_mail(subject, body, DEFAULT_FROM_EMAIL,[to_email], fail_silently=False)
	return True





