from datetime import datetime
import logging
import db

def get_period(time):
	#time is in HH:MM format
	morning_start = 8
	morning_end = 11
	noon_start = 12
	noon_end = 17
	evening_start = 18
	evening_end = 22
	HH = int(time[0:2])
	#logging.warn("HH: %s"%HH)
	if HH >= morning_start and HH <= morning_end:
		return "morning"
	elif HH >= noon_start and HH <= noon_end:
		return "noon"
	elif HH >= evening_start and HH <= evening_end:
		return "evening"
	else:
		return "late"

def get_date_period(date_time):
	f = "%a, %H:%M"
	dt = date_time.strftime(f)
	dt = dt.replace(" ", "")
	dt = dt.split(",")
	p = get_period(dt[1])
	# logging.warn("Current date, day, period: %s, %s, %s"%(dt, dt[0].lower(), p))
	return (dt[0].lower(), p)

def check_trigger(trigger, trigger_type, day, period):
	if trigger['status'][0] != day and trigger['status'][1] != period:
		if trigger['type'] == trigger_type:
			if day in trigger['days']:
				if period in trigger['periods']:
					return True
	return False

def create_trigger(trigger_type, days, periods):
	#logging.warn("%s, %s, %s"%(days, periods, trigger_type))
	i = 0
	for d in days:
		days[i] = d[0:3].lower()
		i += 1
	j = 0
	for p in periods:
		periods[j] = p.lower()
	trigger_type = trigger_type.lower()
	return {"type": trigger_type, "days": days, "periods": periods, "status": [None, None]}