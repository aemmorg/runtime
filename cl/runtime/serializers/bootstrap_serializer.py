# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
from dataclasses import dataclass
from enum import Enum
from typing import Any
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.bool_util import BoolUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.int_util import IntUtil
from cl.runtime.primitive.limits import check_int_32
from cl.runtime.primitive.limits import check_int_54
from cl.runtime.primitive.limits import is_int_32
from cl.runtime.primitive.limits import is_int_54
from cl.runtime.primitive.long_util import LongUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.primitive.uuid_util import UuidUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_empty
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_mapping_type
from cl.runtime.records.protocols import is_sequence_type
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typeof
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.bool_format import BoolFormat
from cl.runtime.serializers.bytes_format import BytesFormat
from cl.runtime.serializers.date_format import DateFormat
from cl.runtime.serializers.datetime_format import DatetimeFormat
from cl.runtime.serializers.encoder import Encoder
from cl.runtime.serializers.enum_format import EnumFormat
from cl.runtime.serializers.float_format import FloatFormat
from cl.runtime.serializers.int_format import IntFormat
from cl.runtime.serializers.key_format import KeyFormat
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.long_format import LongFormat
from cl.runtime.serializers.none_format import NoneFormat
from cl.runtime.serializers.serializer import Serializer
from cl.runtime.serializers.string_format import StringFormat
from cl.runtime.serializers.time_format import TimeFormat
from cl.runtime.serializers.timestamp_format import TimestampFormat
from cl.runtime.serializers.type_format import TypeFormat
from cl.runtime.serializers.type_inclusion import TypeInclusion
from cl.runtime.serializers.type_placement import TypePlacement
from cl.runtime.serializers.uuid_format import UuidFormat


@dataclass(slots=True, kw_only=True)
class BootstrapSerializer(Serializer):
    """Roundtrip serialization of object to a dictionary without type information."""

    none_format: NoneFormat = required()
    """Serialization format for None (pass through without conversion if not set)."""

    string_format: StringFormat = required()
    """Serialization format for str (pass through without conversion if not set)."""

    float_format: FloatFormat = required()
    """Serialization format for float (pass through without conversion if not set)."""

    bool_format: BoolFormat = required()
    """Serialization format for bool (pass through without conversion if not set)."""

    int_format: IntFormat = required()
    """Serialization format for int (pass through without conversion if not set)."""

    long_format: LongFormat = required()
    """Serialization format for long (pass through without conversion if not set)."""

    date_format: DateFormat = required()
    """Serialization format for dt.date (pass through without conversion if not set)."""

    datetime_format: DatetimeFormat = required()
    """Serialization format for dt.datetime (pass through without conversion if not set)."""

    time_format: TimeFormat = required()
    """Serialization format for dt.time (pass through without conversion if not set)."""

    uuid_format: UuidFormat = required()
    """Serialization format for UUID other than UUIDv7 (pass through without conversion if not set)."""

    timestamp_format: TimestampFormat = required()
    """Serialization format for UUIDv7 unique timestamp (pass through without conversion if not set)."""

    bytes_format: BytesFormat = required()
    """Serialization format for bytes (pass through without conversion if not set)."""

    enum_format: EnumFormat = required()
    """Serialization format for enums that are not None."""

    key_format: KeyFormat = required()
    """Serialization format for keys that are not None."""

    encoder: Encoder | None = None
    """Use to encode the output of serialize method if specified."""

    type_inclusion: TypeInclusion = TypeInclusion.OMIT
    """When to include type information in serialized data."""

    type_format: TypeFormat = TypeFormat.DEFAULT
    """Format of the type information in serialized data (optional, not used if type_inclusion=OMIT)."""

    type_placement: TypePlacement = TypePlacement.FIRST
    """Placement of type information in the output dictionary (optional, not used if type_inclusion=OMIT)."""

    type_field: str = "_type"
    """Dictionary key under which type information is stored (optional, defaults to '_type')."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    control_shallow_mode: bool = False
    """If True, controls are processed only one level deep."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize data to a dictionary."""

        # Serialize data to a dictionary without encoding
        serialized = self._serialize(data, type_hint)

        # Encode the result if an encoder is provided
        if self.encoder:
            return self.encoder.encode(serialized)
        else:
            return serialized

    def _serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize data to a dictionary without encoding."""

        data_type_name = type(data).__name__
        if data is None:
            if (value_format := self.none_format) == NoneFormat.PASSTHROUGH:
                # Pass through None for untyped serialization
                return None
            else:
                raise ErrorUtil.enum_value_error(value_format, NoneFormat)
        elif data_type_name == "str":
            # Return None for an empty string
            return data if data else None
        elif data_type_name == "float":
            if (value_format := self.float_format) == FloatFormat.PASSTHROUGH:
                return data
            elif value_format == FloatFormat.DEFAULT:
                return FloatUtil.format(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, FloatFormat)
        elif data_type_name == "bool":
            if (value_format := self.bool_format) == BoolFormat.PASSTHROUGH:
                return data
            elif value_format == BoolFormat.DEFAULT:
                return BoolUtil.to_str_or_none(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, BoolFormat)
        elif data_type_name == "int":
            # Check if the value falls into int32 range
            if is_int_32(data):
                # Check that the value fits into 32-bit signed integer range
                if (value_format := self.int_format) == IntFormat.PASSTHROUGH:
                    check_int_32(data)
                    return data
                elif value_format == IntFormat.DEFAULT:
                    return IntUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, IntFormat)
            elif is_int_54(data):
                # Check that the value fits into 54-bit signed integer range
                if (value_format := self.long_format) == LongFormat.PASSTHROUGH:
                    check_int_54(data)
                    return data
                elif value_format == LongFormat.DEFAULT:
                    return LongUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, LongFormat)
            else:
                raise RuntimeError(f"Value {data} does not fit into 54-bit signed integer range, cannot serialize.")
        elif data_type_name == "date":
            if (value_format := self.date_format) == DateFormat.PASSTHROUGH:
                return data
            elif value_format == DateFormat.DEFAULT:
                return DateUtil.to_iso_str(data)
            elif value_format == DateFormat.COMPACT_STR:
                return DateUtil.to_compact_str(data)
            elif value_format == DateFormat.ISO_INT:
                return DateUtil.to_iso_int(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, DateFormat)
        elif data_type_name == "time":
            if (value_format := self.time_format) == TimeFormat.PASSTHROUGH:
                return data
            elif value_format == TimeFormat.DEFAULT:
                return TimeUtil.to_iso_str(data)
            elif value_format == TimeFormat.ISO_INT:
                return TimeUtil.to_iso_int(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, TimeFormat)
        elif data_type_name == "datetime":
            if (value_format := self.datetime_format) == DatetimeFormat.PASSTHROUGH:
                return data
            elif value_format == DatetimeFormat.DEFAULT:
                return DatetimeUtil.to_iso_str(data)
            elif value_format == DatetimeFormat.COMPACT_STR:
                return DatetimeUtil.to_compact_str(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, DatetimeFormat)
        elif data_type_name == "UUID":
            if data.version != 7:
                # Use UuidFormat for UUID versions other than version 7
                if (value_format := self.uuid_format) == UuidFormat.PASSTHROUGH:
                    return data
                elif value_format == UuidFormat.DEFAULT:
                    # Use the standard delimited UUID format
                    return UuidUtil.to_str(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, UuidFormat)
            else:
                # Use TimestampFormat for UUID version 7
                if (value_format := self.timestamp_format) == TimestampFormat.PASSTHROUGH:
                    return data
                elif value_format == TimestampFormat.DEFAULT:
                    # Use timestamp-hex UUIDv7 format
                    return Timestamp.from_uuid7(data)
                else:
                    raise ErrorUtil.enum_value_error(value_format, TimestampFormat)
        elif data_type_name == "bytes":
            if (value_format := self.bytes_format) == BytesFormat.PASSTHROUGH:
                return data
            elif value_format == BytesFormat.DEFAULT:
                # Base64 encoding for bytes with MIME line wrap convention at 76 characters, remove trailing EOL
                return base64.encodebytes(data).decode("utf-8").rstrip("\n")  # TODO: Create BytesUtil
            elif value_format == BytesFormat.COMPACT:
                # Base64 encoding for bytes on a single line
                return base64.b64encode(data).decode("utf-8")  # TODO: Create BytesUtil
            else:
                raise ErrorUtil.enum_value_error(value_format, BytesFormat)
        elif isinstance(data, type):
            if (value_format := self.type_format) == TypeFormat.PASSTHROUGH:
                # Pass through the type instance without changes
                return data
            elif value_format == TypeFormat.DEFAULT:
                # Serialize as name without type in PascalCase
                return typename(data)
            else:
                raise ErrorUtil.enum_value_error(value_format, TypeFormat)
        elif isinstance(data, Enum):
            if (value_format := self.enum_format) == EnumFormat.PASSTHROUGH:
                # Pass through the enum instance without changes
                return data
            elif value_format == EnumFormat.DEFAULT:
                # Serialize as name without type in PascalCase
                return CaseUtil.upper_to_pascal_case(data.name)
            else:
                raise ErrorUtil.enum_value_error(value_format, EnumFormat)
        elif is_sequence_type(type(data)):
            # Include items that are None in output to preserve item positions
            return [self._serialize(v) if not is_empty(v) else None for v in data]
        elif is_mapping_type(type(data)):
            # Mapping container, do not include values that are None or an empty primitive type
            # Allow keys that begin from _ in mapping classes, but not slotted classes
            return {
                k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k): self._serialize(v)
                for k, v in data.items()
                if not is_empty(v)
            }
        elif is_data_key_or_record_type(type(data)):
            # Use key serializer for key types
            if is_key_type(type(data)):
                if self.key_format == KeyFormat.DELIMITED:
                    key_serializer = KeySerializers.DELIMITED
                    return key_serializer.serialize(data, type_hint)
                elif self.key_format == KeyFormat.TUPLE:
                    key_serializer = KeySerializers.TUPLE
                    return key_serializer.serialize(data, type_hint)
                elif self.key_format == KeyFormat.DEFAULT:
                    # Process keys as data (dict format)
                    pass

            # Data type name taking into account aliases
            data_type_name = typename(type(data))

            # Include type in output according to the type_inclusion setting
            if self.type_inclusion == TypeInclusion.ALWAYS:
                include_type = True
            elif self.type_inclusion == TypeInclusion.AS_NEEDED:
                raise RuntimeError(
                    f"TypeInclusion.AS_NEEDED is not supported for {data_type_name}\n"
                    f"because it does not use a schema."
                )
            elif self.type_inclusion == TypeInclusion.OMIT:
                include_type = False
            else:
                raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusion)

            # Parse type_format field
            if self.type_inclusion not in (None, TypeInclusion.OMIT):
                if self.type_format == TypeFormat.PASSTHROUGH:
                    type_field = type(data)
                elif self.type_format == TypeFormat.DEFAULT:
                    type_field = data_type_name
                else:
                    raise ErrorUtil.enum_value_error(self.type_format, TypeFormat)
            else:
                type_field = None

            # Parse type_placement field
            if self.type_inclusion not in (None, TypeInclusion.OMIT):
                if self.type_placement == TypePlacement.FIRST:
                    include_type_first = include_type
                    include_type_last = False
                elif self.type_placement == TypePlacement.LAST:
                    include_type_first = False
                    include_type_last = include_type
                else:
                    raise ErrorUtil.enum_value_error(self.type_placement, TypePlacement)
            else:
                include_type_first = False
                include_type_last = False

            # Slotted class, get slots from this class and its bases in the order of declaration from base to derived
            slots = data.get_field_names()

            # Include type information first based on include_type_first flag
            result = {self.type_field: type_field} if include_type_first else {}

            # Serialize slot values in the order of declaration except those that are null or empty
            # Allow keys that begin from _ in mapping classes, but not slotted classes
            result.update(
                {
                    k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k): (
                        self._serialize(v) if not self.control_shallow_mode else v
                    )
                    for k in slots
                    if not is_empty(v := getattr(data, k)) and not k.startswith("_")
                }
            )

            if include_type_last:
                # Include type information last based on include_type_last flag
                result[self.type_field] = type_field

            return result
        else:
            # Did not match a supported data type
            raise RuntimeError(f"Cannot serialize data of type '{typename(type(data))}'.")

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a dictionary into object using type information extracted from the _type field."""

        if type_hint is None:
            if is_mapping_type(type(data)):
                # Attempt to extract type information from the mapping data
                if (type_name := data.get(self.type_field, None) if data else None) is not None:
                    # Type name is specified, convert to Python type and look up the class
                    type_ = TypeInfo.from_type_name(type_name)
                    type_spec = TypeSchema.for_type(type_)
                    type_hint = TypeHint.for_type(type_spec.type_)
                else:
                    raise RuntimeError(
                        "Key '_type' is missing in the serialized data and type hint is not specified, "
                        "cannot deserialize."
                    )
            else:
                raise RuntimeError(
                    f"Data is not a list or mapping, cannot deserialize without type_hint argument:\n"
                    f"{ErrorUtil.wrap(data)}."
                )

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type = type_hint.schema_type if type_hint is not None else None

        if is_mapping_type(typeof(data)):
            if schema_type is not None and is_mapping_type(schema_type):
                # Deserialize into mutable dict if schema_type is a mapping
                deserialized_type = dict
            else:
                # Otherwise deserialize as a slotted class
                # Check if serialized data contains _type field
                deserialized_type_name = data.get(self.type_field, None)
                schema_type_name = typename(schema_type) if schema_type is not None else None
                if deserialized_type_name is not None and deserialized_type_name != schema_type_name:
                    # If _type field is present, it must be a subclass of schema_type
                    deserialized_type = TypeInfo.from_type_name(deserialized_type_name)
                    if not issubclass(deserialized_type, schema_type):
                        raise RuntimeError(
                            f"Field _type={deserialized_type_name} in serialized data\n"
                            f"is not a subclass of schema type {typename(schema_type)}."
                        )
                elif schema_type is not None:
                    # Otherwise use schema type if specified
                    deserialized_type = schema_type
                else:
                    raise RuntimeError("Neither schema type nor _type field is provided for a mapping.")

            # Get type spec
            type_spec = TypeSchema.for_type(deserialized_type)
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(f"Type '{typename(deserialized_type)}' cannot be deserialized from a dictionary.")

            # Get class and field dictionary for type_name
            schema_class = type_spec.type_

            # Deserialize into a dict
            result_dict = {
                (
                    CaseUtil.pascale_to_snake_case_keep_trailing_underscore(field_key)
                    if self.pascalize_keys
                    else field_key
                ): field_value
                for field_key, field_value in data.items()
                if not field_key.startswith("_")
            }

            # Construct an instance of the target type
            result = schema_class(**result_dict)

            # Invoke build and return
            return result
        else:
            raise RuntimeError(
                f"Cannot deserialize the following data using type hint '{type_hint.to_str()}':\n"
                f"{ErrorUtil.wrap(data)}"
            )
