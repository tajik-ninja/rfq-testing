"""RFQ API protobuf message types.

Manual protobuf encoding/decoding for the RFQ API messages.
This avoids code generation and external dependencies beyond the standard protobuf library.
"""

from dataclasses import dataclass, field
from typing import Optional

from google.protobuf import json_format
from google.protobuf.internal.encoder import _VarintBytes
from google.protobuf.internal.decoder import _DecodeVarint, _DecodeVarint32


def _encode_varint(value: int) -> bytes:
    """Encode an integer as a varint."""
    return _VarintBytes(value)


def _encode_string(field_num: int, value: str) -> bytes:
    """Encode a string field."""
    if not value:
        return b""
    encoded = value.encode("utf-8")
    # Wire type 2 (length-delimited)
    tag = (field_num << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(encoded)) + encoded


def _encode_uint64(field_num: int, value: int) -> bytes:
    """Encode a uint64 field."""
    if value == 0:
        return b""
    # Handle negative values - they can't be encoded as unsigned varints
    # Treat as 0 (protobuf default) to avoid infinite loop
    if value < 0:
        return b""
    # Wire type 0 (varint)
    tag = (field_num << 3) | 0
    return _encode_varint(tag) + _encode_varint(value)


def _encode_sint64(field_num: int, value: int) -> bytes:
    """Encode a sint64 field (zigzag encoding)."""
    if value == 0:
        return b""
    # Zigzag encode
    encoded_value = (value << 1) ^ (value >> 63)
    tag = (field_num << 3) | 0
    return _encode_varint(tag) + _encode_varint(encoded_value)


def _encode_message(field_num: int, message_bytes: bytes) -> bytes:
    """Encode an embedded message field."""
    if not message_bytes:
        return b""
    tag = (field_num << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(message_bytes)) + message_bytes


# ============================================================
# Core Types
# ============================================================

@dataclass
class RFQRequestType:
    """RFQ request message."""
    rfq_id: int = 0
    market_id: str = ""
    direction: str = ""
    margin: str = ""
    quantity: str = ""
    worst_price: str = ""
    request_address: str = ""
    expiry: int = 0
    status: str = ""
    created_at: int = 0
    updated_at: int = 0
    transaction_time: int = 0
    height: int = 0
    
    def encode(self) -> bytes:
        """Encode to protobuf bytes."""
        result = b""
        result += _encode_uint64(1, self.rfq_id)
        result += _encode_string(2, self.market_id)
        result += _encode_string(3, self.direction)
        result += _encode_string(4, self.margin)
        result += _encode_string(5, self.quantity)
        result += _encode_string(6, self.worst_price)
        result += _encode_string(7, self.request_address)
        result += _encode_uint64(8, self.expiry)
        result += _encode_string(9, self.status)
        result += _encode_sint64(10, self.created_at)
        result += _encode_sint64(11, self.updated_at)
        result += _encode_uint64(12, self.transaction_time)
        result += _encode_uint64(13, self.height)
        return result
    
    @classmethod
    def decode(cls, data: bytes) -> "RFQRequestType":
        """Decode from protobuf bytes."""
        result = cls()
        pos = 0
        while pos < len(data):
            tag_wire, new_pos = _DecodeVarint32(data, pos)
            field_num = tag_wire >> 3
            wire_type = tag_wire & 0x7
            pos = new_pos
            
            if wire_type == 0:  # Varint
                # rfq_id, expiry, transaction_time, height are uint64; use full varint decode
                if field_num in (1, 8, 12, 13):
                    value, pos = _DecodeVarint(data, pos)
                    if field_num == 1:
                        result.rfq_id = value
                    elif field_num == 8:
                        result.expiry = value
                    elif field_num == 12:
                        result.transaction_time = value
                    elif field_num == 13:
                        result.height = value
                else:
                    value, pos = _DecodeVarint32(data, pos)
                    if field_num == 10:
                        # Zigzag decode
                        result.created_at = (value >> 1) ^ -(value & 1)
                    elif field_num == 11:
                        result.updated_at = (value >> 1) ^ -(value & 1)
            elif wire_type == 2:  # Length-delimited
                length, pos = _DecodeVarint32(data, pos)
                value = data[pos:pos + length].decode("utf-8")
                pos += length
                if field_num == 2:
                    result.market_id = value
                elif field_num == 3:
                    result.direction = value
                elif field_num == 4:
                    result.margin = value
                elif field_num == 5:
                    result.quantity = value
                elif field_num == 6:
                    result.worst_price = value
                elif field_num == 7:
                    result.request_address = value
                elif field_num == 9:
                    result.status = value
        
        return result


@dataclass
class RFQQuoteType:
    """RFQ quote message. Encode matches reference injective-indexer proto (api/gen/grpc/injective_rfqrpc/pb):
    1=chain_id, 2=contract_address, 3=market_id, 4=rfq_id, 5=taker_direction, 6=margin, 7=quantity, 8=price,
    9=expiry, 10=maker, 11=taker, 12=signature, 13=status, 14=created_at, 15=updated_at, 16=height,
    17=event_time, 18=transaction_time."""
    market_id: str = ""
    rfq_id: int = 0
    taker_direction: str = ""
    margin: str = ""
    quantity: str = ""
    price: str = ""
    expiry: int = 0
    maker: str = ""
    taker: str = ""
    signature: str = ""
    status: str = ""
    created_at: int = 0
    updated_at: int = 0
    height: int = 0
    event_time: int = 0
    transaction_time: int = 0
    chain_id: str = ""
    contract_address: str = ""

    def encode(self) -> bytes:
        """Encode to protobuf bytes matching reference indexer RFQQuoteType (chain_id=1, rfq_id=4, etc.)."""
        result = b""
        result += _encode_string(1, self.chain_id)
        result += _encode_string(2, self.contract_address)
        result += _encode_string(3, self.market_id)
        result += _encode_uint64(4, self.rfq_id)
        result += _encode_string(5, self.taker_direction)
        result += _encode_string(6, self.margin)
        result += _encode_string(7, self.quantity)
        result += _encode_string(8, self.price)
        result += _encode_uint64(9, self.expiry)
        result += _encode_string(10, self.maker)
        result += _encode_string(11, self.taker)
        result += _encode_string(12, self.signature)
        result += _encode_string(13, self.status)
        result += _encode_sint64(14, self.created_at)
        result += _encode_sint64(15, self.updated_at)
        result += _encode_uint64(16, self.height)
        result += _encode_uint64(17, self.event_time)
        result += _encode_uint64(18, self.transaction_time if self.transaction_time else 0)
        return result

    @classmethod
    def decode(cls, data: bytes) -> "RFQQuoteType":
        """Decode from protobuf bytes (reference indexer field order: 1=chain_id, 2=contract_address, 4=rfq_id, ...)."""
        result = cls()
        pos = 0
        while pos < len(data):
            tag_wire, new_pos = _DecodeVarint32(data, pos)
            field_num = tag_wire >> 3
            wire_type = tag_wire & 0x7
            pos = new_pos

            if wire_type == 0:  # Varint
                if field_num in (4, 9, 16, 17, 18):
                    value, pos = _DecodeVarint(data, pos)
                    if field_num == 4:
                        result.rfq_id = value
                    elif field_num == 9:
                        result.expiry = value
                    elif field_num == 16:
                        result.height = value
                    elif field_num == 17:
                        result.event_time = value
                    elif field_num == 18:
                        result.transaction_time = value
                else:
                    value, pos = _DecodeVarint32(data, pos)
                    if field_num == 14:
                        result.created_at = (value >> 1) ^ -(value & 1)
                    elif field_num == 15:
                        result.updated_at = (value >> 1) ^ -(value & 1)
            elif wire_type == 2:  # Length-delimited
                length, pos = _DecodeVarint32(data, pos)
                value = data[pos:pos + length].decode("utf-8")
                pos += length
                if field_num == 1:
                    result.chain_id = value
                elif field_num == 2:
                    result.contract_address = value
                elif field_num == 3:
                    result.market_id = value
                elif field_num == 5:
                    result.taker_direction = value
                elif field_num == 6:
                    result.margin = value
                elif field_num == 7:
                    result.quantity = value
                elif field_num == 8:
                    result.price = value
                elif field_num == 10:
                    result.maker = value
                elif field_num == 11:
                    result.taker = value
                elif field_num == 12:
                    result.signature = value
                elif field_num == 13:
                    result.status = value

        return result


@dataclass
class StreamAck:
    """Acknowledgment for stream operations."""
    rfq_id: int = 0
    status: str = ""
    
    @classmethod
    def decode(cls, data: bytes) -> "StreamAck":
        """Decode from protobuf bytes."""
        result = cls()
        pos = 0
        while pos < len(data):
            tag_wire, new_pos = _DecodeVarint32(data, pos)
            field_num = tag_wire >> 3
            wire_type = tag_wire & 0x7
            pos = new_pos
            
            if wire_type == 0:
                # rfq_id is uint64
                value, pos = _DecodeVarint(data, pos)
                if field_num == 1:
                    result.rfq_id = value
            elif wire_type == 2:
                length, pos = _DecodeVarint32(data, pos)
                value = data[pos:pos + length].decode("utf-8")
                pos += length
                if field_num == 2:
                    result.status = value

        return result


@dataclass
class StreamError:
    """Error message in stream."""
    code: str = ""
    message: str = ""
    
    @classmethod
    def decode(cls, data: bytes) -> "StreamError":
        """Decode from protobuf bytes."""
        result = cls()
        pos = 0
        while pos < len(data):
            tag_wire, new_pos = _DecodeVarint32(data, pos)
            field_num = tag_wire >> 3
            wire_type = tag_wire & 0x7
            pos = new_pos
            
            if wire_type == 2:
                length, pos = _DecodeVarint32(data, pos)
                value = data[pos:pos + length].decode("utf-8")
                pos += length
                if field_num == 1:
                    result.code = value
                elif field_num == 2:
                    result.message = value
        
        return result


@dataclass
class CreateRFQRequestType:
    """Create-request message (no request_address; server uses connection metadata).

    Matches indexer proto CreateRFQRequestType: fields 1–12.
    Use this for TakerStream 'request' messages; server sets request_address from stream metadata.
    """
    rfq_id: int = 0
    market_id: str = ""
    direction: str = ""
    margin: str = ""
    quantity: str = ""
    worst_price: str = ""
    expiry: int = 0
    status: str = ""
    created_at: int = 0
    updated_at: int = 0
    transaction_time: int = 0
    height: int = 0

    def encode(self) -> bytes:
        """Encode to protobuf bytes (field numbers match indexer CreateRFQRequestType)."""
        result = b""
        result += _encode_uint64(1, self.rfq_id)
        result += _encode_string(2, self.market_id)
        result += _encode_string(3, self.direction)
        result += _encode_string(4, self.margin)
        result += _encode_string(5, self.quantity)
        result += _encode_string(6, self.worst_price)
        result += _encode_uint64(7, self.expiry)
        result += _encode_string(8, self.status)
        result += _encode_sint64(9, self.created_at)
        result += _encode_sint64(10, self.updated_at)
        result += _encode_uint64(11, self.transaction_time)
        result += _encode_uint64(12, self.height)
        return result


# ============================================================
# Taker Stream Messages
# ============================================================

@dataclass
class TakerStreamRequest:
    """Message sent by taker in bidirectional stream."""
    message_type: str = ""  # "ping" | "request"
    # For "request" use CreateRFQRequestType (server gets request_address from stream metadata)
    request: Optional[RFQRequestType] = None  # type: ignore[assignment]  # also CreateRFQRequestType

    def encode(self) -> bytes:
        """Encode to protobuf bytes."""
        result = b""
        result += _encode_string(1, self.message_type)
        if self.request is not None:
            result += _encode_message(2, self.request.encode())
        return result


@dataclass
class TakerStreamResponse:
    """Message received by taker from server."""
    message_type: str = ""  # "pong" | "quote" | "request_ack" | "error"
    quote: Optional[RFQQuoteType] = None
    request_ack: Optional[StreamAck] = None
    error: Optional[StreamError] = None
    stream_operation: str = ""
    
    @classmethod
    def decode(cls, data: bytes) -> "TakerStreamResponse":
        """Decode from protobuf bytes."""
        result = cls()
        pos = 0
        while pos < len(data):
            if pos >= len(data):
                break
            tag_wire, new_pos = _DecodeVarint32(data, pos)
            field_num = tag_wire >> 3
            wire_type = tag_wire & 0x7
            pos = new_pos
            
            if wire_type == 2:  # Length-delimited
                length, pos = _DecodeVarint32(data, pos)
                value_bytes = data[pos:pos + length]
                pos += length
                
                if field_num == 1:
                    result.message_type = value_bytes.decode("utf-8")
                elif field_num == 2:
                    result.quote = RFQQuoteType.decode(value_bytes)
                elif field_num == 3:
                    result.request_ack = StreamAck.decode(value_bytes)
                elif field_num == 4:
                    result.error = StreamError.decode(value_bytes)
                elif field_num == 5:
                    result.stream_operation = value_bytes.decode("utf-8")
        
        return result


# ============================================================
# Maker Stream Messages
# ============================================================

@dataclass
class MakerStreamRequest:
    """Message sent by maker in bidirectional stream."""
    message_type: str = ""  # "ping" | "quote"
    quote: Optional[RFQQuoteType] = None
    
    def encode(self) -> bytes:
        """Encode to protobuf bytes."""
        result = b""
        result += _encode_string(1, self.message_type)
        if self.quote:
            result += _encode_message(2, self.quote.encode())
        return result


@dataclass
class MakerStreamResponse:
    """Message received by maker from server."""
    message_type: str = ""  # "pong" | "request" | "quote_ack" | "error"
    request: Optional[RFQRequestType] = None
    quote_ack: Optional[StreamAck] = None
    error: Optional[StreamError] = None
    stream_operation: str = ""
    
    @classmethod
    def decode(cls, data: bytes) -> "MakerStreamResponse":
        """Decode from protobuf bytes."""
        result = cls()
        pos = 0
        while pos < len(data):
            if pos >= len(data):
                break
            tag_wire, new_pos = _DecodeVarint32(data, pos)
            field_num = tag_wire >> 3
            wire_type = tag_wire & 0x7
            pos = new_pos
            
            if wire_type == 2:  # Length-delimited
                length, pos = _DecodeVarint32(data, pos)
                value_bytes = data[pos:pos + length]
                pos += length
                
                if field_num == 1:
                    result.message_type = value_bytes.decode("utf-8")
                elif field_num == 2:
                    result.request = RFQRequestType.decode(value_bytes)
                elif field_num == 3:
                    result.quote_ack = StreamAck.decode(value_bytes)
                elif field_num == 4:
                    result.error = StreamError.decode(value_bytes)
                elif field_num == 5:
                    result.stream_operation = value_bytes.decode("utf-8")
        
        return result
