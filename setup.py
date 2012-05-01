from setuptools import setup

setup(
    name='Hawthorne'
    , version='1.0'
    , long_description=__doc__
    , packages=['hawthorne']
    , include_package_data=True
    , zip_safe=False
    , install_requires=[
        'Flask==0.8'
        , 'Flask-Bcrypt==0.5.2'
        , 'Jinja2==2.6'
        , 'Werkzeug==0.8.3'
        , 'boto==2.2.2'
        , 'lettuce==0.1.35'
        , 'mongoengine==0.5.2'
        , 'py-bcrypt==0.2'
        , 'pymongo==2.1.1'
        , 'wsgiref==0.1.2'
    ]
)
