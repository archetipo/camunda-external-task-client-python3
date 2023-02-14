import json
import inflection
from typing import Any, Dict, List, Tuple, Union
from datetime import date, datetime
from dateutil import parser

LATEST = "__latest__"
JSONPrimitive = Union[str, int, None, float]
ProcessVariable = Dict[str, JSONPrimitive]  # {"type": "Integer", "value": 42}
ProcessVariables = Dict[str, ProcessVariable]


def get_base64(strinin):
    bytemsg = base64.b64encode(strinin.encode('utf-8'))
    tokenb64 = str(bytemsg, "utf-8")
    return tokenb64


def parse_definition(definition_ref: str) -> Tuple[bool, str]:
    """
    Given a definition reference, parse it to determine if it's a specific version.
    """
    bits = definition_ref.split(":")
    if len(bits) == 2 and bits[1] == LATEST:
        return True, bits[0]
    return False, definition_ref


def noop(val):
    return val


def underscoreize(data: Union[List, Dict, str, None]) -> Union[List, Dict, str, None]:
    if isinstance(data, list):
        return [underscoreize(item) for item in data]

    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = inflection.underscore(key)
            # variables are dynamic names, can't make assumptions!
            if key == "variables":
                new_data[new_key] = value
            else:
                new_data[new_key] = underscoreize(value)
        return new_data

    return data


def try_is_json(value):
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception as e:
        return value


TYPE_MAP = {
    bool: ("Boolean", noop),
    date: (
        "String",
        lambda d: d.isoformat(),
    ),  # Date object requires time information, which we don't have
    datetime: ("Date", lambda d: d.isoformat()),
    int: ("Integer", noop),
    float: ("Double", noop),
    str: ("String", noop),
    type(None): ("Null", noop),
    dict: ("Json", json.dumps),
    list: ("Json", json.dumps),
}

REVERSE_TYPE_MAP = {
    "date": parser.parse,
    "json": try_is_json,
    "integer": int,
    "boolean": bool,
    "short": int,
    "long": int,
    "double": float,
    "string": str,
}


class Variables:
    def __init__(self, variables={}):
        self.variables = variables

    @classmethod
    def deserialize_variable(cls, variable: ProcessVariable) -> Any:
        if not variable:
            return None
        if with_meta:
            return variable
        var_type = variable.get("type", "String")
        converter = REVERSE_TYPE_MAP.get(var_type.lower())
        value = converter(variable["value"])
        value = try_is_json(value)
        return value

    @classmethod
    def serialize_variable(cls, value: Any) -> ProcessVariable:
        val_type = type(value)
        if val_type not in TYPE_MAP:
            raise NotImplementedError(f"Type {val_type} is not implemented yet")

        type_name, converter = TYPE_MAP[val_type]
        value = converter(value)
        return {"type": type_name, "value": value}

    def get_variable(self, variable_name, with_meta=False):

        return self.deserialize_variable(self.variables.get(variable_name))

    @classmethod
    def format(cls, variables):
        """
        Gives the correct format to variables.
        :param variables: dict - Dictionary of variable names to values.
        :return: Dictionary of well formed variables
            {"var1": 1, "var2": True}
            ->
            {"var1": {"value": 1, "type": "Integer"}, "var2": {"value": True, "type":"Boolean"}}
        """
        formatted_vars = {}
        if variables:
            formatted_vars = {
                k: cls.serialize_variable(v) for k, v in variables.items()
            }
        return formatted_vars

    def to_dict(self):
        """
        Converts the variables to a simple dictionary
        :return: dict
            {"var1": {"value": 1, "type":"Integer"}, "var2": {"value": True, "type":"Boolean"}}
            ->
            {"var1": 1, "var2": True}
        """
        result = {
            k: self.deserialize_variable(v) for k, v in self.variables.items()
        }
        return result
