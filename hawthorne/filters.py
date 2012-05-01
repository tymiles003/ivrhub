''' jinja filters
formatters of sorts
'''
from flask import (request, session, abort)

from hawthorne import app
import utilities


@app.template_filter('_format_datetime')
def _format_datetime(dt, formatting='medium'):
    ''' jinja filter for displaying datetimes
    usage in the jinja template:
        publication date: {{ article.pub_date|_format_datetime('full') }}
    '''
    if formatting == 'full':
        return dt.strftime('%A %B %d, %Y at %H:%M:%S')
    if formatting == 'medium':
        return dt.strftime('%B %d, %Y at %H:%M:%S')
    if formatting == 'full-day':
        return dt.strftime('%A %B %d, %Y')
    if formatting == 'short-date-with-time':
        return dt.strftime('%m/%d/%y %H:%M:%S')
    if formatting == 'day-month-year':
        return dt.strftime('%B %d, %Y')
    if formatting == 'hours-minutes-seconds':
        return dt.strftime('%H:%M:%S')

@app.before_request
def csrf_protect():
    ''' CSRF protection via http://flask.pocoo.org/snippets/3/
    '''
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            if not app.config['TESTING']:
                app.logger.error('bad CSRF token')
                abort(403)

def _generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = utilities.generate_random_string(24)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = _generate_csrf_token
