# VS lab

## How to use

Generell:
- open Docker Desktop
- open terminal
 - cd to repo folder
 - docker-compose up --build --scale boerse=1 --scale bank=4

Workaround for following Error *Error response from daemon: driver failed programming external connectivity on endpoint vs-praktikum-bank-1 (19a4a9a43ed074d42706cf0a0f4ee6dc3a035b9713626b66b4d2149065a073b7): Bind for 0.0.0.0:22100 failed: port is already allocated*
- open docker-compose.yml
- bank: ports. 22100 (random port for multiple instances)

P1:
- see UDP communication in terminal

P2:
- click on port of one bank in Docker Desktop Container
- add /kundenportal or /mitarbeiterportal to the url -> should look e.g. so: *http://localhost:51349/kundenportal*
- have fun while playing with our kunden-/mitarbeiterportal

## Components

### Bank

### Boerse

### Lookup

This is a simple Lookup server. Services can register themselves and clients can lookup the server address.

Each service is identified id chosen by the service itself. The service registers what ip and port it is listening on and what type of service it is.

The client can then lookup the service type and get all available services of a certain type.

All communication is using json. The endpoints are:

- POST	
	- /register
    - /keepalive
	- /unregister
- GET	
	- /services
	- /services?type=\<type\>
	- /service/\<id\>
