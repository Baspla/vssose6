from http.server import BaseHTTPRequestHandler, HTTPServer
import logging as log
import os

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

def start_server():
    port = int(os.environ.get("PORT", 12340))
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    log.info('Starting server on port %s' % port)
    httpd.serve_forever()


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        log.info("Received GET request")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("Hello World", "utf-8"))

    def do_POST(self):
        log.info("Received POST request")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("Hello World", "utf-8"))

    def log_message(self, format, *args):
        log.debug("%s - - [%s] %s %s %s %s" % (self.client_address[0], self.log_date_time_string(), self.command, self.path, self.request_version, format%args))
    
