from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, Subgroup, View
from datetime import datetime, timedelta
import glob
import os
import platform
import subprocess

##
# Setup the Flask application.
##
catfeeder = { \
	'path': os.path.join(os.environ['HOME'], 'projects/catfeeder/catfeeder.py'),
	'time': '0.16',
	'output': os.path.join(os.environ['HOME'], '.log/catfeeder.txt')
	}
app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)

@nav.navigation('katty_navbar')
def create_navbar():
	'''
	Create the navigation bar.
	'''

	homeView = View('Home', 'index')
	liveStreamView = View('Live Stream', 'live_stream')
	galleryView = View('Gallery', 'gallery')
	#aboutView = View('About', 'about')
	return Navbar('Katty', homeView, liveStreamView, galleryView)
	#return Navbar('Katty', homeView, liveStreamView, galleryView, aboutView)

@app.route('/')
def index():
	'''
	Home page.
	'''

	return render_template('index.html')

@app.route('/live')
def live_stream():
	'''
	Live stream of my cat.
	'''

	return render_template('livestream.html')

@app.route('/gallery')
def gallery():
	'''
	Gallery of recent times my cat has been fed.
	'''

	directory = os.path.join(app.static_folder, 'img')
	now = datetime.now()
	images = []

	for delta in range(8):
			date = now - timedelta(days=delta)
			nameformat = '{0}*'.format(date.strftime('%Y%m%d_'))
			filepath = os.path.join(directory, nameformat)
			listing = [os.path.basename(f) for f in glob.glob(filepath)]

			listing.sort()
			images.append((delta, date.strftime('%a, %b %-d'), list(enumerate(listing))))

	return render_template('gallery.html', gallery=images)

#@app.route('/about')
#def about():
#	return render_template('index.html')

@app.route('/ctrl')
def controller():
	'''
	Control the cat feeder.
	'''

	return render_template('controller.html')

@app.route('/cw')
def feeder_cw():
	'''
	Spin the feeder clockwise.
	'''

	cmd = '{0} -t {1} -d CW -o {2}'.format(catfeeder['path'], catfeeder['time'],
		catfeeder['output'])
	subprocess.call(cmd, shell=True)
	return '', 204

@app.route('/ccw')
def feeder_ccw():
	'''
	Spin the feeder counter-clockwise.
	'''

	cmd = '{0} -t {1} -d CCW -o {2}'.format(catfeeder['path'], catfeeder['time'],
		catfeeder['output'])
	subprocess.call(cmd, shell=True)
	return '', 204

@app.route('/skip')
def feeder_skip():
	'''
	Skip the next feeding time.
	'''

	cmd = '{0} --skip -o {1}'.format(catfeeder['path'], catfeeder['output'])
	subprocess.call(cmd, shell=True)
	return '', 204

@app.route('/unskip')
def feeder_unskip():
	'''
	Unskip the next feeding time.
	'''

	cmd = '{0} --unskip -o {1}'.format(catfeeder['path'], catfeeder['output'])
	subprocess.call(cmd, shell=True)
	return '', 204

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=False)
