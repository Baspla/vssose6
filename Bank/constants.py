#
# Constants
#
import uuid


PRINT_PRICES_INTERVAL = 45
TIMEOUT = 30
BUFFER_SIZE = 1024
FILE_PATH = 'static/stocks_amounts.csv'
START_FUNDS = 100000
START_LOANS = 0
PRINT_PRICES = False
LOOKUP_KEEPALIVE_INTERVAL = 15
SERVER_ID = str(uuid.uuid4())
INSOLVENCY_THRESHOLD = 10000
FINANCECHECK_INTERVAL = 10
INSOLVENCY_LENDING_AMOUNT = 10000
GRPC_MEASUREMENTS = 10
PUBLISH_VALUES_INTERVAL = 10
INSOLVENCY_LENDING_AMOUNT_MQTT = 50000