from flask import Flask, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, Subgroup, View
from datetime import datetime, timedelta

import glob
import os
import platform
import re
import subprocess
import sys

##
# Setup the Flask application.
##
catfeeder = { \
	"path": os.path.join(os.environ["HOME"], "projects/catfeeder/catfeeder.py"),
	"time": "0.16",
	"output": os.path.join(os.environ["HOME"], ".log/catfeeder.txt")
	}
app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)

@nav.navigation("katty_navbar")
def create_navbar():
	"""
	Create the navigation bar.
	"""

	# Home
	homeView = View("Home", "index")

	# Stream
	liveStreamView = View("Live Stream", "live_stream")
	multiStreamView = View("Multi Stream", "multi_stream")
	streamView = Subgroup("Stream", liveStreamView, multiStreamView)

	# Gallery
	feederGalleryView = View("Feeder", "gallery_feeder")
	motionTrackerGalleryView = View("Motion Tracker", "gallery_motion_tracker")
	galleryView = Subgroup("Gallery", feederGalleryView, motionTrackerGalleryView)

	# Temps
	tempsView = View("Temps", "temps_monitor")

	# About
	#aboutView = View("About", "about")

	return Navbar("Katty", homeView, streamView, galleryView, tempsView)
	#return Navbar("Katty", homeView, liveStreamView, galleryView, aboutView)

@app.route("/")
def index():
	"""
	Home page.
	"""

	return render_template("index.html")

#@app.route("/about")
#def about():
#	return render_template("index.html")

@app.route("/ctrl")
def controller():
	"""
	Control the cat feeder.
	"""

	return render_template("controller.html")

def convert_request_to_timespan():
	"""
	Convert the request arguments to a timespan.
	"""

	ndays = 0

	if "span" in request.args:
		span = request.args.get("span")

		if span == "today":
			ndays = 0
		elif span == "1d":
			ndays = 1
		elif span == "2d":
			ndays = 2
		elif span == "3d":
			ndays = 3
		else:
			pass

	return ndays

@app.route("/cw")
def feeder_cw():
	"""
	Spin the feeder clockwise.
	"""

	cmd = "{0} -t {1} -d CW -o {2}".format(catfeeder["path"], catfeeder["time"],
		catfeeder["output"])
	subprocess.call(cmd, shell=True)

	return render_template("controller_cw.html")
	#return "", 204

@app.route("/ccw")
def feeder_ccw():
	"""
	Spin the feeder counter-clockwise.
	"""

	cmd = "{0} -t {1} -d CCW -o {2}".format(catfeeder["path"], catfeeder["time"],
		catfeeder["output"])
	subprocess.call(cmd, shell=True)

	return render_template("controller_ccw.html")
	#return "", 204

@app.route("/skip")
def feeder_skip():
	"""
	Skip the next feeding time.
	"""

	cmd = "{0} --skip -o {1}".format(catfeeder["path"], catfeeder["output"])
	subprocess.call(cmd, shell=True)

	return render_template("controller_skip.html")
	#return "", 204

@app.route("/unskip")
def feeder_unskip():
	"""
	Unskip the next feeding time.
	"""

	cmd = "{0} --unskip -o {1}".format(catfeeder["path"], catfeeder["output"])
	subprocess.call(cmd, shell=True)

	return render_template("controller_unskip.html")
	#return "", 204

@app.route("/gallery/feeder")
def gallery_feeder():
	"""
	Gallery of recent times my cat has been fed.
	"""

	directory = os.path.join(app.static_folder, "pics/feeder")
	now = datetime.now()
	images = []

	for delta in range(8):
		date = now - timedelta(days=delta)
		nameformat = "{0}*".format(date.strftime("%Y%m%d_"))
		filepath = os.path.join(directory, nameformat)
		listing = [os.path.basename(f) for f in glob.glob(filepath)]

		listing.sort()
		images.append((delta, date.strftime("%a, %b %-d"), list(enumerate(listing))))

	return render_template("gallery_feeder.html", gallery=images)

@app.route("/gallery/motiontracker")
def gallery_motion_tracker():
	"""
	Gallery of motion tracker events.
	"""

	directory = os.path.join(app.static_folder, "pics/motiontracker")
	filepath = "{0}/*.webp".format(directory)
	daylist = list( \
		set( \
			[os.path.basename(f)[0:8] for f in glob.glob(filepath)] \
			))
	daylist.sort()
	calendar = []

	for d in daylist:
		filepath = "{0}/{1}*.webp".format(directory, d)
		filelist = [os.path.basename(f) for f in glob.glob(filepath)]
		filelist.sort()

		day = []
		events = []
		previous = ""

		for f in filelist:
			if f[0:11] != previous:
				if events:
					day.append(events)
				events = []

			events.append(f)
			previous = f[0:11]

		calendar.append([d[0:4], d[4:6], d[6:8], day])

	#for d in calendar:
	#	print d[0], d[1], d[2]
	#	for e in d[3]:
	#		print e
	#	print

	return render_template("gallery_motiontracker.html")

@app.route("/live")
def live_stream():
	"""
	Live stream of my cat.
	"""

	# Default IP address
	ipaddr = "127.0.0.1"

	# Read the IP address that is stored in a temp file by a separate process
	with open("/tmp/ipaddr.tmp", "r") as handle:
		ipaddr = handle.read().strip()

	return render_template("livestream.html", ipaddr=ipaddr)

@app.route("/multi")
def multi_stream():
	"""
	Multi stream of my cat.
	"""

	ipaddr = "127.0.0.1"
	with open("/tmp/ipaddr.tmp", "r") as handle:
		ipaddr = handle.read().strip()
	return render_template("multistream.html", ipaddr=ipaddr)

def read_temp_log(filepath, ndays):
	"""
	Read a temperature log.
	"""

	# File does not exist
	if not os.path.isfile(filepath):
		return ([], [])

	now = datetime.now()
	timestamps = []
	temps = []

	# Read a file line by line
	with open(filepath, "r") as handle:

		for line in handle:
			line = line.strip().replace("[", "")
			timestr, tempstr = line.split("]")

			# Make sure line can be converted to datetime
			try:
				date = datetime.strptime(timestr, "%Y-%m-%d %H:%M:%S %Z")
				delta = now - date
			except ValueError:
				continue

			# Skip every 5 min
			if (date.minute % 5) != 0:
				continue

			# Only look at temps from today
			if ndays == 0 and delta.days == 0 and now.day == date.day:
				pass

			# Only look at temps within some number of days from today
			elif delta.days >= ndays:
				continue

			# Convert to a better timestamp and temp
			betterTimestamp = date.strftime("%a %b %d  %H:%M %Z")
			betterTemp = tempstr.replace("temp=", "").replace("'C", "").strip()

			# Store these better timestamp and temp values
			timestamps.append(betterTimestamp)
			temps.append(betterTemp)

	return (timestamps, temps)

@app.route("/temp")
def temp_monitor():
	"""
	Redirect /temps to /temp.
	"""

	return redirect(url_for("temps_monitor"))

@app.route("/temps")
def temps_monitor():
	"""
	Monitor temperature of cameras.
	"""

	home = os.getenv("HOME")
	dirpath = os.path.join(home, "katty", "static/temps")
	ndays = convert_request_to_timespan()

	# red purple blue green 
	rgbColors = ["#fc4c68", "#67074e", "#00579a", "#3eb489"]
	ncolors = len(rgbColors)
	
	# Store all data here
	allNames = []
	allTimestamps = []
	allTemps = []
	allColors = []
	
	# Store individual camera data here
	timestamps = []
	temps = []
	index = 0

	# Each subdirectory corresponds to a camera
	for d in sorted(os.listdir(dirpath)):
		subdir = os.path.join(dirpath, d)

		if not os.path.isdir(subdir):
			continue

		# Get the name of the camera
		name = re.sub('(\d+(\.\d+)?)', r' \1 ', d.capitalize())

		# Look at the temps of each camera
		filepath = os.path.join(subdir, "temp.log")
		timestamps, temps = read_temp_log(filepath, ndays)

		# Save the timestamps and temps for each camera so they can be plotted
		allNames.append(name)
		allTimestamps.append(timestamps)
		allTemps.append(temps)
		allColors.append(rgbColors[index % ncolors])

		index += 1

	return render_template("temps_monitor.html", zip=zip, allNames=allNames,
		allTimestamps=allTimestamps, allTemps=allTemps, allColors=allColors)

if __name__ == "__main__":
	app.run()
	#app.run(host="0.0.0.0", debug=False)
