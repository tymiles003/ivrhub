''' vanilla_views
some of the more boring routes
'''
from flask import (render_template)

from ivrhub import app


@app.route('/')
def home():
    ''' home page, how fun
    '''
    return render_template('home.html')


@app.route('/about')
def about():
    ''' show the about page
    '''
    return render_template('about.html')


@app.route('/help')
def help():
    ''' show the help page
    '''
    return render_template('help.html')


@app.route('/demo')
def demo():
    ''' show the demo video
    '''
    return render_template('demo.html')


''' error pages
'''
@app.errorhandler(404)
def page_not_found(error):
    ''' replaces stock 404 page
    '''
    return render_template('error_404.html'), 404


@app.errorhandler(500)
def server_error(error):
    ''' replaces stock 500 page
    '''
    return render_template('error_500.html'), 500
