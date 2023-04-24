#
# Load Börsen Server from Lookup Server
# 
# This function is called when the bank starts up
# It tries to find a boerse server in the lookup server
# If it fails, it retries with exponential backoff
#
import os
import socket
import http.client
import json
import logging as log
import time
import uuid
from constants import LOOKUP_KEEPALIVE_INTERVAL, SERVER_ID

from configuration import LOOKUP_HOST, LOOKUP_PORT

def load_server(type):
    
    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)

    headers = {
        "Content-Type": "application/json"
    }

    run = True
    server = []

    attempt = 0

    while run:
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("GET", "/services?type="+type,None, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    if data["services"].__len__() > 0:
                        server = data["services"]
                        log.info("Successfully retrieved "+type+" server from lookup service.")
                        run = False
                    else:
                        log.warning("No "+type+" server found in lookup service. Response: {}".format(data))
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
    return server

def load_boersen_server():
    return load_server("boerse")

def load_bank_server():
    return load_server("bank")


def register_bank_at_lookup(ip,port):
    id = SERVER_ID
    data = {
        "id": id,
        "ip": ip,
        "port": port,
        "type": "bank"
    }

    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)

    payload = json.dumps(data)

    headers = {
        "Content-Type": "application/json"
    }

    run = True

    attempt = 0
    
    while run:
        conn = None
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("POST", "/register", payload, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    log.info("Successfully registered with lookup service. Response: {}".format(data))
                    run = False
            if run:
                log.error(f"Registration failed with HTTP status code {response.status} {response.reason} and data {data}")
        except Exception as e:
            log.error(f"Error: {e}")
        finally:
            if conn:
                conn.close()
        if run:
            # exponential backoff up to a maximum of 1 minute
            backoff = min(2 ** (attempt + 1), 60)
            attempt += 1
            log.debug(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)    
    return id

def lookup_keepalive(id, ip, port):
    data = {
        "id": id,
        "ip": ip,
        "port": port,
        "type": "bank"
    }

    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)

    payload = json.dumps(data)

    headers = {
        "Content-Type": "application/json"
    }

    while True:
        time.sleep(LOOKUP_KEEPALIVE_INTERVAL)
        conn = None
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("POST", "/register", payload, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    log.info("Successfully re-registered with lookup service. Response: {}".format(data))
                else:
                    log.error(f"Re-registration failed. Response: {data}")
            else:
                log.error(f"Re-registration failed with HTTP status code {response.status} {response.reason} and data {data}")
        except Exception as e:
            log.error(f"Error: {e}")
        finally:
            if conn:
                conn.close()