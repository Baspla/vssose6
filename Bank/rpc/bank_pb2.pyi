from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Request(_message.Message):
    __slots__ = ["amount", "bank"]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    BANK_FIELD_NUMBER: _ClassVar[int]
    amount: float
    bank: str
    def __init__(self, bank: _Optional[str] = ..., amount: _Optional[float] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ["reason", "status"]
    REASON_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    reason: str
    status: str
    def __init__(self, status: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...
