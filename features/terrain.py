from hawthorne import app, views
from lettuce import before, after, world
from pymongo import Connection

@before.all
def setup_flask_test_client():
    app.config['TESTING'] = True

    # setup test db by modifying db name from config
    app.config['MONGO_CONFIG']['db_name'] += '_testing'
    
    # make sure it doesn't already exists
    # teardown's not cleaning up properly, it seems..
    connection = Connection(app.config['MONGO_CONFIG']['host']
        , app.config['MONGO_CONFIG']['port'])
    connection.drop_database(app.config['MONGO_CONFIG']['db_name'])

    # populate the db
    views.seed()
    
    world.app = app.test_client()


@after.all
def teardown(total):
    # drop the mongo db
    connection = Connection(app.config['MONGO_CONFIG']['host']
        , app.config['MONGO_CONFIG']['port'])
    connection.drop_database(app.config['MONGO_CONFIG']['db_name'])
