import os
# if os.path.exists('.env'):
#     print('Importing environment from .env...')
#     for line in open('.env')
#         var = line.strip().split('=')
#         if len(var) == 2:
#             os.environ[var[0]] = var[1]

# cov = None
# if os.environ.get('FLASK_COVERAGE'):
#     import coverage
#     cov = coverage.coverage(branch=True, include='app/*')
#     cov.start()

from app import create_app, db
from app.models import Provider, ProviderBranch, ProviderBranchEmployee, TrainingBatch, TrainingSession, TrainingSessionAssistant, User
from flask.ext.script import Manager, Shell
from gunicorn.app.base import Application

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


def make_shell_context():
    return dict(    app=app,
                    db=db, 
                    Provider=Provider,
                    ProviderBranch=ProviderBranch,
                    ProviderBranchEmployee=ProviderBranchEmployee,
                    TrainingBatch=TrainingBatch,
                    TrainingSession=TrainingSession,
                    TrainingSessionAssistant=TrainingSessionAssistant,
                    User=User)

manager.add_command('shell', Shell(make_context=make_shell_context))
# manager.add_command('db', MigrateCommand)


@manager.option('-h', '--host', dest='host', default='0.0.0.0')
@manager.option('-p', '--port', dest='port', type=int, default=5000)
@manager.option('-w', '--workers', dest='workers', type=int, default=10)
@manager.option('-t', '--timeout', dest='timeout', type=int, default=90)
def gunicorn(host, port, workers, timeout):
    """Start the Server with Gunicorn"""
    from gunicorn.app.base import Application

    class FlaskApplication(Application):
        def init(self, parser, opts, args):
            return {
                'bind': '{0}:{1}'.format(host, port),
                'workers': workers, 'timeout': timeout

            }

        def load(self):
            return app

    application = FlaskApplication()
    return application.run()


@manager.command
def profile(length=25, profile_dir=None):
    """Start de application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
    app.run()


if __name__ == '__main__':
    manager.run()