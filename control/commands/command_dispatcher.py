#!/usr/bin/env python3
"""
Command Dispatcher - Central command registry and execution dispatcher
Author: Pito Salas and Claude Code
Open Source Under MIT license
"""
import control.commands.command_def as cd
import control.commands.control_commands as ctrl_cmd
import control.commands.intent_commands as intent_cmd
import control.commands.launch_commands as lch_cmd
import control.commands.movement_commands as mov_cmd
import control.commands.navigation_commands as nav_cmd
import control.commands.parameter_def as paramdef_mod
import control.commands.robot_controller as rc
import control.commands.semantic_commands as sem_cmd
import control.commands.system_commands as sys_cmd


class CommandDispatcher:
    """
    Unified command dispatcher for CLI, TUI, and REST API interfaces.
    Provides standardized parameter handling and response format.
    """

    def __init__(self, robot_controller):
        self.robot_controller = robot_controller
        self.commands = self._build_command_registry()

    def _build_command_registry(self) -> dict[str, cd.CommandDef]:
        commands = {}
        commands.update(mov_cmd.build_movement_commands())
        commands.update(ctrl_cmd.build_control_commands())
        commands.update(nav_cmd.build_navigation_commands())
        commands.update(lch_cmd.build_launch_commands())
        commands.update(sys_cmd.build_system_commands())
        commands.update(intent_cmd.build_intent_commands())
        commands.update(sem_cmd.build_semantic_commands())
        return commands

    def execute(
        self, command_name: str, params: dict[str, object]
    ) -> rc.CommandResponse:
        if command_name not in self.commands:
            return rc.CommandResponse(
                success=False, message=f"Unknown command: {command_name}"
            )

        command_def = self.commands[command_name]

        try:
            validated_params = self._validate_parameters(command_def, params)
        except ValueError as e:
            return rc.CommandResponse(
                success=False, message=f"Parameter error: {e!s}"
            )

        try:
            method = getattr(self.robot_controller, command_def.method_name)
        except AttributeError:
            return rc.CommandResponse(
                success=False, message=f"Method {command_def.method_name} not found"
            )

        try:
            if validated_params:
                result = method(**validated_params)
            else:
                result = method()

            if isinstance(result, rc.CommandResponse):
                return result
            return rc.CommandResponse(
                success=True,
                message=str(result) if result is not None else "Command completed",
            )

        except Exception as e:
            return rc.CommandResponse(
                success=False, message=f"Command execution error: {e!s}"
            )

    def _validate_parameters(
        self, command_def: cd.CommandDef, params: dict[str, object]
    ) -> dict[str, object]:
        validated = {}

        for param_def in command_def.parameters:
            param_name = param_def.name

            if param_def.required and param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")

            if param_name not in params:
                if param_def.default is not None:
                    validated[param_name] = param_def.default
                continue

            value = params[param_name]
            try:
                validated[param_name] = self._convert_parameter_value(param_def, value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid type for {param_name}: expected {param_def.param_type.__name__}, got {type(value).__name__}"
                )

        return validated

    def _convert_parameter_value(
        self, param_def: paramdef_mod.ParameterDef, value: object
    ) -> object:
        if param_def.param_type == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        if param_def.param_type == str:
            return str(value)
        return param_def.param_type(value)

    def list_commands(self, group: str | None = None) -> list[str]:
        if group:
            return [
                name
                for name, cmd_def in self.commands.items()
                if cmd_def.group == group
            ]
        return list(self.commands.keys())

    def get_command_info(self, command_name: str) -> cd.CommandDef | None:
        return self.commands.get(command_name)

    def get_groups(self) -> list[str]:
        groups = {cmd_def.group for cmd_def in self.commands.values()}
        return sorted(groups)
