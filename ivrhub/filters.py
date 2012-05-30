''' jinja filters
formatters of sorts
'''
from ivrhub import app


@app.template_filter('abbreviate')
def abbreviate(word, length, remove='end'):
    ''' turns long phrases into something like 'asdf123..'
    the 'remove' parameter determines which part of the string to drop
    usage in jinja template:
        call ID: {{ response.call_sid }}
        call ID: {{ response.call_sid|abbreviate(7, remove='start') }}
    yields something like:
        call ID: SIDabcdefgh1234
        call ID: ..fgh1234
    '''
    if not word:
        return word
    
    word = str(word)
    if len(word) <= length:
        return word

    if remove == 'start':
        # drop the beginning of the word
        return '..' + word[len(word)-length:]
    else:
        # drop the end
        return word[0:length] + '..'


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
