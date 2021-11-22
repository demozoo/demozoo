import os

import dotenv
from django.core.wsgi import get_wsgi_application


dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
application = get_wsgi_application()
