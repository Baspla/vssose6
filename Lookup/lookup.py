import json
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging as log

#
# Set up logging
#
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
log.basicConfig(
    level=LOGLEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        log.FileHandler('debug.log'),
        log.StreamHandler()
    ]
)

# Helper function to get current time in milliseconds
def current_time():
    return int(round(time.time() * 1000))

class RequestHandler(BaseHTTPRequestHandler):    

    #
    # Helper functions
    #
    def ok_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def error_headers(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def respond_with_json(self, message):
        self.wfile.write(json.dumps(message).encode())

    def load_json_data(self):
        if 'Content-Length' not in self.headers:
            return None
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)
        return data

    #
    # This overrides the default logging function, so that we can control the log level
    #
    def log_message(self, format, *args):
        log.debug("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format%args))
        return

    #
    # Handle GET requests
    #
    def do_GET(self):
        if self.path == '/':

            self.ok_headers()
            # Serve json with all endpoints
            message = { "ok": True, "endpoints": {"POST": ["/register", "/unregister"], "GET": ["/services", "/services?type=<type>", "/service/<id>"] }}
            self.respond_with_json(message)
        
        # Serve a simple form for debugging
        elif self.path == '/debug':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('postform.html', 'r') as f:
                self.wfile.write(f.read().encode())

        # Return a json list of all services filtered by type
        elif self.path.startswith('/services?type='):
            self.ok_headers()
            # Lookup service by type
            service_type = self.path.split('=')[1]
            filtered_services = {}
            for key, value in services.items():
                if value['type'] == service_type:
                    filtered_services[key] = value
            
            message = { "ok": True, "services": filtered_services }
            self.respond_with_json(message)

        # Return a json list of all services
        elif self.path.startswith('/services'):

            self.ok_headers()
            # List all services
            message = { "ok": True, "services": services }
            self.respond_with_json(message)

        # Return a json object of a single service
        elif self.path.startswith('/service/'):

            self.ok_headers()
            # Lookup service by id
            service_id = self.path.split('/')[2]
            if service_id in services:
                message = { "ok": True, "service": services[service_id] }
            else:
                message = { "ok": False, "error": "Service not found" }
            self.respond_with_json(message)

        # Return an error because no service id was provided
        elif self.path == '/service':
                
                self.error_headers(400)
                # Send 400 in json format
                message = { "ok": False, "error": "Missing service id" }
                self.respond_with_json(message)

        # This is the default case for all other paths
        else:
            # Send 404 in json format
            self.error_headers(404)
            message = { "ok": False, "error": "Not found" }
            self.respond_with_json(message)

        return
    
    #
    # Handle POST requests
    #
    def do_POST(self):
        if self.path == '/register':

            self.ok_headers()
            # Register service
            data = self.load_json_data()
            if 'id' in data and 'type' in data and 'ip' in data and 'port' in data:
                if data['id'] == '':
                    message = { "ok": False,"method":"register", "error": "Missing id" }
                elif data['ip'] == '':
                    message = { "ok": False,"method":"register", "error": "Missing ip" }
                elif data['port'] == '':
                    message = { "ok": False,"method":"register", "error": "Missing port" }
                else:
                    overwrite = False
                    if data['id'] in services:
                        overwrite = True
                    services[data['id']] = { 'type': data['type'], 'ip': data['ip'], 'port': data['port'], 'last_seen': current_time() }
                    message = { "ok": True,"method":"register", "overwritten": overwrite}
            else:
                message = { "ok": False,"method":"register", "error": "Missing data" }
            self.respond_with_json(message)

        elif self.path == '/unregister':

            self.ok_headers()
            # Unregister service
            data = self.load_json_data()
            if 'id' in data:
                if data['id'] in services:
                    del services[data['id']]
                    message = { "ok": True , "method": "unregister"}
                else:
                    message = { "ok": False, "method": "unregister", "error": "Service not found" }
            self.respond_with_json(message)
        else:

            # Send 404 in json format
            self.error_headers(404)
            message = { "ok": False, "error": "Not found" }
            self.respond_with_json(message)

        return

#
# Periodically clean up services that have not been seen for a while
#
def clean_up():
    while True:
        time.sleep(CLEANUP_INTERVAL)
        log.info("Cleaning up services")
        to_delete = []
        for key, value in services.items():
            if current_time() - value['last_seen'] > (CLEANUP_TTL*1000):
                to_delete.append(key)
        for key in to_delete:
            log.info("Removing service {}".format(key))
            try:
                del services[key]
            except:
                pass

services = {}

#
# Constants
#
CLEANUP_INTERVAL = 30
CLEANUP_TTL = 90

#
# Main
#
if __name__ == "__main__":
    # Clean up services that have not been seen for a while
    t1 = threading.Thread(target=clean_up).start()
    port = int(os.environ.get("PORT", 12340))
    server = HTTPServer(('', port), RequestHandler)
    log.info("Started lookup server on port {}".format(port))
    server.serve_forever()