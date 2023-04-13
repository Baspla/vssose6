import json
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

services = {}

def current_time():
    return int(round(time.time() * 1000))

class RequestHandler(BaseHTTPRequestHandler):    

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

    def do_GET(self):
        if self.path == '/':

            self.ok_headers()
            # Serve json with all endpoints
            message = { "ok": True, "endpoints": {"POST": ["/register","/keepalive", "/unregister"], "GET": ["/services", "/services?type=<type>", "/service/<id>"] }}
            self.respond_with_json(message)
        
        elif self.path == '/debug':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('Lookup/postform.html', 'r') as f:
                self.wfile.write(f.read().encode())

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

        elif self.path.startswith('/services'):

            self.ok_headers()
            # List all services
            message = { "ok": True, "services": services }
            self.respond_with_json(message)

        elif self.path.startswith('/service/'):

            self.ok_headers()
            # Lookup service by id
            service_id = self.path.split('/')[2]
            if service_id in services:
                message = { "ok": True, "service": services[service_id] }
            else:
                message = { "ok": False, "error": "Service not found" }
            self.respond_with_json(message)

        elif self.path == '/service':
                
                self.error_headers(400)
                # Send 400 in json format
                message = { "ok": False, "error": "Missing service id" }
                self.respond_with_json(message)

        else:

            # Send 404 in json format
            self.error_headers(404)
            message = { "ok": False, "error": "Not found" }
            self.respond_with_json(message)

        return
    
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

        elif self.path == '/keepalive':

            self.ok_headers()
            # Keep service alive
            data = self.load_json_data()
            if 'id' in data:
                if data['id'] in services:
                    services[data['id']]['last_seen'] = current_time()
                    message = { "ok": True, "method":"keepalive" }
                else:
                    message = { "ok": False, "method":"keepalive", "error": "Service not found" }
            else:
                message = { "ok": False, "method":"keepalive", "error": "Missing data" }
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

def clean_up():
    while True:
        time.sleep(60)
        for key, value in services.items():
            if current_time() - value['last_seen'] > 300000:
                del services[key]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 12340))
    server = HTTPServer(('', port), RequestHandler)
    print("Started server on port {}".format(port))
    server.serve_forever()

    # Clean up services that have not been seen for 5 minutes
    t1 = threading.Thread(target=clean_up)