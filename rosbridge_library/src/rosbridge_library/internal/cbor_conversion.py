import struct

try:
    from cbor import Tag
except ImportError:
    from rosbridge_library.util.cbor import Tag


LIST_TYPES = [list, tuple]
INT_TYPES = [
    "byte",
    "char",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "octet",
]
FLOAT_TYPES = ["float32", "float64", "float", "double"]
STRING_TYPES = ["string"]
BOOL_TYPES = ["bool","boolean"]
TIME_TYPES = ["time", "duration"]
BOOL_ARRAY_TYPES = ["sequence<boolean>"]
STRING_ARRAY_TYPES = ["sequence<string>"]
BYTESTREAM_TYPES = ["sequence<uint8>", "sequence<char>"]

# Typed array tags according to <https://tools.ietf.org/html/draft-ietf-cbor-array-tags-00>
# More cbor tags info can be found here <https://www.iana.org/assignments/cbor-tags/cbor-tags.xhtml>
# Structs info can be found here <https://docs.python.org/3/library/struct.html>
# Always encode to little-endian variant, for now.
TAGGED_ARRAY_FORMATS = {
    "uint16[]": (69, "<{}H"),
    "uint32[]": (70, "<{}I"),
    "uint64[]": (71, "<{}Q"),
    "byte[]": (72, "{}b"),
    "int8[]": (72, "{}b"),
    "uint8[]": (64, "{}B"),
    "sequence<byte>": (72, "{}b"),
    "sequence<int8>": (72, "{}b"),
    "sequence<uint8>": (64, "{}B"),
    "sequence<int16>": (77, "<{}h"),
    "sequence<uint16>": (69, "<{}H"),
    "sequence<int32>": (78, "<{}i"),
    "sequence<uint32>": (70, "<{}I"),
    "sequence<int64>": (79, "<{}q"),
    "sequence<uint64>": (71, "<{}Q"),
    "sequence<float32>": (85, "<{}f"),
    "sequence<float64>": (86, "<{}d"),
    "sequence<float>": (85, "<{}f"),
    "sequence<double>": (86, "<{}d"),
    "int16[]": (77, "<{}h"),
    "int32[]": (78, "<{}i"),
    "int64[]": (79, "<{}q"),
    "float32[]": (85, "<{}f"),
    "float64[]": (86, "<{}d"),
}


def extract_cbor_values(msg):
    """Extract a dictionary of CBOR-friendly values from a ROS message.

    Primitive values will be casted to specific Python primitives.

    Typed arrays will be tagged and packed into byte arrays.
    """
    out = {}
    for slot, slot_type in msg.get_fields_and_field_types().items():
        val = getattr(msg, slot)

        # string
        if slot_type in STRING_TYPES:
            out[slot] = str(val)

        # bool
        elif slot_type in BOOL_TYPES:
            out[slot] = bool(val)

        # integers
        elif slot_type in INT_TYPES:
            out[slot] = int(val)

        # floats
        elif slot_type in FLOAT_TYPES:
            out[slot] = float(val)

        # time/duration
        elif slot_type in TIME_TYPES:
            out[slot] = {
                "sec": int(val.sec),
                "nanosec": int(val.nanosec),
            }

        # byte array
        elif slot_type in BYTESTREAM_TYPES:
            out[slot] = bytes(val)

        # bool array
        elif slot_type in BOOL_ARRAY_TYPES:
            out[slot] = [bool(i) for i in val]

        elif slot_type in STRING_ARRAY_TYPES:
            out[slot] = [str(i) for i in val]

        # numeric arrays
        elif slot_type in TAGGED_ARRAY_FORMATS:
            tag, fmt = TAGGED_ARRAY_FORMATS[slot_type]
            fmt_to_length = fmt.format(len(val))
            packed = struct.pack(fmt_to_length, *val)
            out[slot] = Tag(tag=tag, value=packed)

        # array of messages
        elif type(val) in LIST_TYPES:
            out[slot] = [extract_cbor_values(i) for i in val]

        # message
        else:
            out[slot] = extract_cbor_values(val)

    return out
