#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Set, Union

from normalization import data_type
from normalization.transform_catalog import dbt_macro


def jinja_call(command: Union[str, dbt_macro.Macro]) -> str:
    return "{{ " + command + " }}"


def remove_jinja(command: str) -> str:
    return str(command).replace("{{ ", "").replace(" }}", "")


# transform oneOf nested list ot plain types list
def get_plain_list_from_one_of_array(one_of_definition) -> list:
    one_of_property = one_of_definition[data_type.ONE_OF_VAR_NAME]
    plain_datatypes_list = list()
    for prop in one_of_property:
        plain_datatypes_list.append(prop[data_type.REF_TYPE_VAR_NAME])
    return plain_datatypes_list


def is_string(property_type) -> bool:
    if data_type.ONE_OF_VAR_NAME in property_type:
        return bool(
            any(option[data_type.REF_TYPE_VAR_NAME] == data_type.STRING_TYPE for option in property_type[data_type.ONE_OF_VAR_NAME])
        )
    else:
        return property_type == data_type.STRING_TYPE or data_type.STRING_TYPE in property_type


def is_binary_datatype(property_type) -> bool:
    return property_type == data_type.BINARY_DATA_TYPE or data_type.BINARY_DATA_TYPE in property_type


def is_datetime(definition: dict) -> bool:
    return is_datetime_with_timezone(definition) or is_datetime_without_timezone(definition)


def is_datetime_without_timezone(definition: dict) -> bool:
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(
            any(
                option[data_type.REF_TYPE_VAR_NAME] == data_type.TIMESTAMP_WITHOUT_TIMEZONE_TYPE
                for option in definition[data_type.ONE_OF_VAR_NAME]
            )
        )
    else:
        return bool(data_type.TIMESTAMP_WITHOUT_TIMEZONE_TYPE == definition[data_type.REF_TYPE_VAR_NAME])


def is_datetime_with_timezone(definition: dict) -> bool:
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(
            any(
                option[data_type.REF_TYPE_VAR_NAME] == data_type.TIMESTAMP_WITH_TIMEZONE_TYPE
                for option in definition[data_type.ONE_OF_VAR_NAME]
            )
        )
    else:
        return bool(data_type.TIMESTAMP_WITH_TIMEZONE_TYPE == definition[data_type.REF_TYPE_VAR_NAME])


def is_date(definition: dict) -> bool:
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(any(option[data_type.REF_TYPE_VAR_NAME] == data_type.DATE_TYPE for option in definition[data_type.ONE_OF_VAR_NAME]))
    else:
        return bool(data_type.DATE_TYPE == definition[data_type.REF_TYPE_VAR_NAME])


def is_time(definition: dict) -> bool:
    return is_time_with_timezone(definition) or is_time_without_timezone(definition)


def is_time_with_timezone(definition: dict) -> bool:
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(
            any(
                option[data_type.REF_TYPE_VAR_NAME] == data_type.TIME_WITH_TIME_ZONE_TYPE
                for option in definition[data_type.ONE_OF_VAR_NAME]
            )
        )
    else:
        return bool(data_type.TIME_WITH_TIME_ZONE_TYPE == definition[data_type.REF_TYPE_VAR_NAME])


def is_time_without_timezone(definition: dict) -> bool:
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(
            any(
                option[data_type.REF_TYPE_VAR_NAME] == data_type.TIME_WITHOUT_TIME_ZONE_TYPE
                for option in definition[data_type.ONE_OF_VAR_NAME]
            )
        )
    else:
        return bool(data_type.TIME_WITHOUT_TIME_ZONE_TYPE == definition[data_type.REF_TYPE_VAR_NAME])


def is_number(property_type) -> bool:
    if is_string(property_type):
        # Handle union type, give priority to wider scope types
        return False
    if data_type.ONE_OF_VAR_NAME in property_type:
        return bool(
            any(option[data_type.REF_TYPE_VAR_NAME] == data_type.NUMBER_TYPE for option in property_type[data_type.ONE_OF_VAR_NAME])
        )
    else:
        return property_type == data_type.NUMBER_TYPE or data_type.NUMBER_TYPE in property_type


# this is obsolete type that will not be used in new datatypes
def is_big_integer(definition: dict) -> bool:
    return False


def is_long(property_type, definition: dict) -> bool:
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(
            any(option[data_type.REF_TYPE_VAR_NAME] == data_type.INTEGER_TYPE for option in property_type[data_type.ONE_OF_VAR_NAME])
        )
    else:
        return property_type == data_type.INTEGER_TYPE or data_type.INTEGER_TYPE in property_type


def is_boolean(property_type, definition: dict) -> bool:
    if is_string(property_type) or is_number(property_type) or is_big_integer(definition) or is_long(property_type, definition):
        # Handle union type, give priority to wider scope types
        return False
    if data_type.ONE_OF_VAR_NAME in definition:
        return bool(
            any(option[data_type.REF_TYPE_VAR_NAME] == data_type.BOOLEAN_TYPE for option in property_type[data_type.ONE_OF_VAR_NAME])
        )
    else:
        return property_type == data_type.BOOLEAN_TYPE or data_type.BOOLEAN_TYPE in property_type


def is_array(property_type) -> bool:
    return property_type == "array" or "array" in property_type


def is_object(property_type) -> bool:
    return property_type == "object" or "object" in property_type


def is_airbyte_column(name: str) -> bool:
    return name.startswith("_airbyte_")


def is_simple_property(definition: dict) -> bool:
    if data_type.REF_TYPE_VAR_NAME not in definition and data_type.ONE_OF_VAR_NAME not in definition:
        property_type = "object"
    elif data_type.ONE_OF_VAR_NAME in definition and data_type.ONE_OF_VAR_NAME in definition:
        property_type = definition
    else:
        property_type = definition[data_type.REF_TYPE_VAR_NAME]
    return (
        is_string(property_type)
        or is_binary_datatype(property_type)
        or is_big_integer(definition)
        or is_long(property_type, definition)
        or is_number(property_type)
        or is_boolean(property_type, definition)
    )


def is_combining_node(properties: dict) -> Set[str]:
    # this case appears when we have analog of old protocol like id: {type:[number, string]} and it's handled separately
    if data_type.ONE_OF_VAR_NAME in properties and len(properties[data_type.ONE_OF_VAR_NAME]) > 0:
        if data_type.REF_TYPE_VAR_NAME in properties[data_type.ONE_OF_VAR_NAME][0]:
            return set()
    else:
        return set(properties).intersection({"anyOf", "oneOf", "allOf"})
