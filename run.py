#!/usr/bin/env python
from hawthorne import app

app.run(
    host = app.config['APP_IP']
    , port = app.config['APP_PORT']
)
