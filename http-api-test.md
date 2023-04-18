Endpoint: /api/

HTTP-Methode: GET

Testdaten:

Erwartetes Ergebnis:

Tatsächliches Ergebnis:



Endpoint: /api/totalValue

HTTP-Methode: GET

Testdaten:

Erwartetes Ergebnis: {"totalValue":"5842413.33"}

Tatsächliches Ergebnis: {"totalValue":"5842413.33"}


Endpoint: /api/totalFunds

HTTP-Methode: GET

Testdaten:

Erwartetes Ergebnis: {"totalFunds": 100000}

Tatsächliches Ergebnis: {"totalFunds": 100000}


Endpoint: /api/totalLoans

HTTP-Methode: GET

Testdaten:
Vorher wurde ein Loan von 100 genommen

Erwartetes Ergebnis: {"totalLoans": 100.0}

Tatsächliches Ergebnis: {"totalLoans": 100.0}


Endpoint: /api/totalPortfolio

HTTP-Methode: GET

Testdaten:

Erwartetes Ergebnis: {"totalPortfolio": 5742413.33}

Tatsächliches Ergebnis: {"totalPortfolio": 5742413.33}



Endpoint: /api/stockList

HTTP-Methode: GET

Testdaten:

Erwartetes Ergebnis: Stock List stimmt mit internen Arrays überein (über log.info ausgegeben)

Tatsächliches Ergebnis: Stock List stimmt überein.


Endpoint: /api/deposit

HTTP-Methode: POST

Testdaten:
{"amount":"100"}

Erwartetes Ergebnis: totalFunds wird um 100 erhöht.

Tatsächliches Ergebnis: totalFunds wurde um 100 erhöht.

Testdaten:
{"amount":"-100"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Bad Request

Testdaten:
{"amount":"h_da"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 500 Internal Server Error


Endpoint: /api/withdraw

HTTP-Methode: Post

Testdaten:
{"amount":"100"}

Erwartetes Ergebnis: totalFunds wird um 100 verringert.

Tatsächliches Ergebnis: totalFunds wurde um 100 verringert.

Testdaten:
{"amount":"-100"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Bad Request

Testdaten:
{"amount":"h_da"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 500 Internal Server Error


Endpoint: /api/getLoan

HTTP-Methode: POST

Testdaten:
{"amount":"100"}

Erwartetes Ergebnis: totalFunds wird um 100 verringert. totalLoans wird um 100 erhöht.

Tatsächliches Ergebnis: totalFunds wurde um 100 verringert und totalLoans um 100 erhöht.

Testdaten:
{"amount":"-100"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Bad Request

Testdaten:
{"amount":"h_da"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 500 Internal Server Error


Endpoint: /api/repayLoan

HTTP-Methode: GET

Testdaten:
{"amount":"100"}

Erwartetes Ergebnis: totalFunds wird um 100 erhöht. totalLoans wird um 100 verringert.

Tatsächliches Ergebnis: totalFunds wurde um 100 erhöht und totalLoans um 100 verringert.

Testdaten:
{"amount":"-100"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Bad Request

Testdaten:
{"amount":"h_da"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 500 Internal Server Error


Endpoint: /api/buyStock

HTTP-Methode: GET

Testdaten:
{"amount":"1","name":"WKN1"}

Erwartetes Ergebnis: totalFunds wird um 7.37 (Preis von WKN1) verringert. Anzahl von amount["WKN1"] wird um 1 erhöht.

Tatsächliches Ergebnis: totalFunds wurder verringert und amount erhöht.

Testdaten:
{"amount":"-1","name":"WKN1"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Bad Request

Testdaten:
{"amount":"h_da","name":"WKN1"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 500 Internal Server Error



Endpoint: /api/sellStock

HTTP-Methode: GET

Testdaten:
{"amount":"1","name":"WKN1"}

Erwartetes Ergebnis: totalFunds wird um 7.37 (Preis von WKN1) erhöht. Anzahl von amount["WKN1"] wird um 1 verringert.

Tatsächliches Ergebnis: totalFunds wurder erhöht und amount verringert.

Testdaten:
{"amount":"1","name":"h_da"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 500 Internal Server Error

Testdaten:
{"amount":"1","name":"WKN1"}

Erwartetes Ergebnis: totalFunds wird um 7.37 (Preis von WKN1) erhöht. Anzahl von amount["WKN1"] wird um 1 verringert.

Tatsächliches Ergebnis: totalFunds wurder erhöht und amount verringert.

Testdaten:
{"amount":"-1","name":"WKN1"}

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Bad Request

Testdaten:
{"amount":"1","name":"WKN1"}
Es sind aber keine Stocks mehr da.

Erwartetes Ergebnis: Ein Fehler wird zurückgegeben

Tatsächliches Ergebnis: Fehler 400 Not enough stocks

