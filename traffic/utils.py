from parse_rest.user import User
from parse_rest.datatypes import Object, Date

import datetime
from dateutil.parser import parse
import urllib2
import urllib
import json
import pprint
#from scipy.stats import percentileofscore

class TestEvent(Object):
    pass

class EventSizePercentile(Object):
    pass

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

def pullEvents(location, date):
	
	# set date ranges
	date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
	beg_date = date - datetime.timedelta(days=1)
	end_date = date + datetime.timedelta(days=5)
	parse_beg_date = Date(beg_date)
	parse_end_date = Date(end_date)

	# run Parse query
	events = TestEvent.Query.all().filter(City=location, StartDate__gte=parse_beg_date, EndDate__lte=parse_end_date, Lat__gte=-10000000, Lng__gte=-100000000)
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
				k.pretty_full_Time = "%s - %s" % (pretty_StartTime, pretty_EndTime)
				
				# add item to events list
				events_split[date.date()].append(k)
	
	sorted_keys = sorted(events_split.keys())
	
	capacities_query = EventSizePercentile.Query.all().filter(City=location)
	capacities_query = capacities_query.order_by("createdAt").limit(1)
	
	for c in capacities_query:
		capacities = c
	
	# turn dic into sorted list for easy iteration on client side
	percentiles = []
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
	for i in caps:
		percentiles.append(calc_percentile(caps, i))
	
	return (sorted_keys, events_sorted, events_split, percentiles)	


def daily_event_size(location):
	
	# this determines typical size and number of events in an area to determine if a date is relatively busy or slow
	# to-do: update to only consider historical and most recently acquired data

	# run Parse query
	date = datetime.datetime.now()
	date = Date(datetime.datetime(date.year, date.month, date.day, 0, 0, 0))
	events_query = TestEvent.Query.all().filter(StartDate__lte=date)
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
