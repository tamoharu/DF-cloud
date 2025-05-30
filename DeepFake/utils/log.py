from typing import Dict
from logging import basicConfig, getLogger, Logger, DEBUG, INFO, WARNING, ERROR

import DeepFake.config.globals as globals
import DeepFake.config.type as type


def init(log_level: type.LogLevel) -> None:
	basicConfig(format = None) #type: ignore
	get_package_logger().setLevel(get_log_levels()[log_level])


def get_package_logger() -> Logger:
	return getLogger(globals.PJ_NAME)


def debug(message: str, scope: str) -> None:
	get_package_logger().debug('[' + scope + '] ' + message)


def info(message: str, scope: str) -> None:
	get_package_logger().info('[' + scope + '] ' + message)


def warn(message: str, scope: str) -> None:
	get_package_logger().warning('[' + scope + '] ' + message)


def error(message: str, scope: str) -> None:
	get_package_logger().error('[' + scope + '] ' + message)


def enable() -> None:
	get_package_logger().disabled = False


def disable() -> None:
	get_package_logger().disabled = True


def get_log_levels() -> Dict[type.LogLevel, int]:
	return\
	{
		'error': ERROR,
		'warn': WARNING,
		'info': INFO,
		'debug': DEBUG
	}
