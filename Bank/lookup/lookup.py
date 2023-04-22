#
# Load Börsen Server from Lookup Server
# 
# This function is called when the bank starts up
# It tries to find a boerse server in the lookup server
# If it fails, it retries with exponential backoff
#
import socket
import http.client
import json
import logging as log
import time

from configuration import LOOKUP_HOST, LOOKUP_PORT

def load_boersen_server():
    
    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)

    headers = {
        "Content-Type": "application/json"
    }

    run = True
    boersen = []

    attempt = 0

    while run:
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("GET", "/services?type=boerse",None, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    if data["services"].__len__() > 0:
                        boersen = data["services"]
                        log.info("Successfully retrieved boerse server from lookup service.")
                        run = False
                    else:
                        log.warning("No boerse server found in lookup service. Response: {}".format(data))
            if run:
                log.error(f"Failed to find boersen server with HTTP status code {response.status} {response.reason} and data {data}")
        except Exception as e:
            log.error(f"Error: {e}")
            
        if run:
            # exponential backoff up to a maximum of 1 minute
            backoff = min(2 ** (attempt + 1), 60)
            attempt += 1
            log.debug(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
    return boersen