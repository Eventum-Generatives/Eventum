import importlib
from abc import ABC
from typing import Any, Literal, Protocol

from eventum_plugins.utils.modules import get_module_names
from pydantic import BaseModel, Field, create_model, model_validator
from pytz.tzinfo import DstTzInfo


class MutexFieldsModel(ABC, BaseModel, extra='forbid', frozen=True):
    @model_validator(mode='after')
    def validate_mutual_exclusion(self):
        """Validate that only one field is passed and rest fields is `None`."""
        values = [
            self.__getattribute__(field) for field in self.model_fields.keys()
        ]

        if values.count(None) == (len(values) - 1):
            return self

        raise ValueError('Only one key can be defined at this level')

    def get_name(self) -> str:
        """Get name of used parameter."""
        return list(filter(
            lambda attr: self.__getattribute__(attr) is not None,
            self.model_fields.keys()
        )).pop()

    def get_value(self) -> Any:
        """Get value if used parameter."""
        return self.__getattribute__(self.get_name())


def get_plugins_to_config_mapping(
    plugin_type: Literal['input', 'output']
) -> dict[str, BaseModel]:
    """Get mapping where keys are a plugin names and values are config
    classes for specified types of plugins."""
    mapping: dict[str, BaseModel] = dict()
    for module_name in get_module_names(f'eventum_plugins.{plugin_type}'):
        module = importlib.import_module(
            name=f'eventum_plugins.{plugin_type}.{module_name}'
        )
        try:
            mapping[module_name] = module.CONFIG_CLASS
        except AttributeError:
            pass

    return mapping


class PluggableAsInput(Protocol):
    def __init__(self, config: Any, tz: DstTzInfo) -> None:
        pass


class PluggableAsOutput(Protocol):
    def __init__(self, config: Any) -> None:
        pass


def load_plugin_class(
    plugin_type: Literal['input', 'output'],
    plugin_name: str
) -> type[PluggableAsInput] | type[PluggableAsOutput]:
    """Get plugin class. Raise `ValueError` if plugin with specified
    name is not found."""
    try:
        module = importlib.import_module(
            name=f'eventum_plugins.{plugin_type}.{plugin_name}'
        )
        return module.PLUGIN_CLASS
    except (ModuleNotFoundError, AttributeError):
        raise ValueError(
            f'{plugin_type.capitalize()} plugin "{plugin_name}" is not found'
        )


InputConfigMapping: type[
    MutexFieldsModel
] = create_model(               # type: ignore[call-overload]
    'InputConfigMapping',
    __base__=MutexFieldsModel,
    __cls_kwargs__={'frozen': True},
    **{
        plugin_name: (config_class, Field(None))
        for plugin_name, config_class in get_plugins_to_config_mapping(
            plugin_type='input'
        ).items()
    }
)

OutputConfigMapping: type[
    MutexFieldsModel
] = create_model(               # type: ignore[call-overload]
    'OutputConfigMapping',
    __base__=MutexFieldsModel,
    __cls_kwargs__={'frozen': True},
    **{
        plugin_name: (config_class, Field(None))
        for plugin_name, config_class in get_plugins_to_config_mapping(
            plugin_type='output'
        ).items()
    }
)