from serve.hawthorne_server import app
from lettuce import before, after, world

@before.all
def setup_flask_test_client():
    # setup test db by modifying db name from config
    app.config['MONGO_CONFIG']['db_name'] += '_testing'
    
    world.app = app.test_client()

    # run the init script
    #hawthorne_server.init()

    #hawthorne_server.app.config['TESTING'] = True
    #self.app = hawthorne_server.app.test_client()

@after.all
def teardown(total):
    pass
