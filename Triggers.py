from datetime import datetime
import logging

def get_period(time):
	#time is in HH:MM format
	morning_start = 8
	morning_end = 11
	noon_start = 12
	noon_end = 5
	evening_start = 6
	evening_end = 10
	HH = int(time[0:2])
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
	dt.strip(" ")
	dt = dt.split(",")
	p = get_period(dt[1])
	return (dt[0].lower(), p)

def check_trigger(trigger, trigger_type, dt):
	days, periods = get_date_period(dt)
	if trigger['type'] == trigger_type and days and periods:
		for day in days:
			if day in trigger['days']:
				for p in periods:
					if p in trigger['periods']:
						return True
	return False

def create_trigger(trigger_type, days, periods):
	# logging.warn("%s, %s, %s"%(days, periods, trigger_type))
	return {"type": trigger_type, "days": days, "periods": periods, "status": False}