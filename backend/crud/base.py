from functools import wraps

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_db_operation(operation_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    logger.info(f"Successfully {operation_name}")
                else:
                    logger.warning(f"Failed to {operation_name} - not found")
                return result
            except Exception as e:
                logger.error(f"Error during {operation_name}: {e}")
                if "db" in kwargs:
                    kwargs["db"].rollback()
                raise

        return wrapper

    return decorator
