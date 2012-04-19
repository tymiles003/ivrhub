from serve.hawthorne_server import app, init
from lettuce import before, after, world
from pymongo import Connection

@before.all
def setup_flask_test_client():
    app.config['TESTING'] = True

    # setup test db by modifying db name from config
    app.config['MONGO_CONFIG']['db_name'] += '_testing'
    # populate the db
    init()
    
    world.app = app.test_client()


@after.all
def teardown(total):
    # drop the mongo db
    connection = Connection(app.config['MONGO_CONFIG']['host']
        , app.config['MONGO_CONFIG']['port'])
    connection.drop_database(app.config['MONGO_CONFIG']['db_name'])
