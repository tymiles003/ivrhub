#!/usr/bin/env python
'''
upload_server.py
uploading sample data and performing some basic parsing
'''
import flask

app = flask.Flask(__name__)
app.config.from_envvar('HAWTHORNE_SETTINGS')


@app.route('/')
def home():
    return flask.render_template('home.html')



if __name__ == '__main__':
    app.run(
        host=app.config['APP_IP']
        , port=app.config['APP_PORT']
    )
