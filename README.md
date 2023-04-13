# vs-praktikum
Vereinigtes repo für das ganze Praktikum


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
