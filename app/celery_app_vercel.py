"""
Stub do Celery para Vercel (serverless).
O Celery não funciona no ambiente serverless, então criamos um stub que loga as tasks.
"""

from loguru import logger


class FakeCeleryTask:
    """Task falsa que apenas loga a chamada."""
    def __init__(self, func, name):
        self.func = func
        self.name = name
        self.__wrapped__ = func

    def __call__(self, *args, **kwargs):
        logger.info(f"[CELERY-STUB] Task {self.name} chamada com args={args}, kwargs={kwargs}")
        return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        logger.info(f"[CELERY-STUB] Task {self.name}.delay() chamada")
        return {"task_id": "stub-task", "status": "completed"}

    def apply_async(self, *args, **kwargs):
        logger.info(f"[CELERY-STUB] Task {self.name}.apply_async() chamada")
        return {"task_id": "stub-task", "status": "completed"}


class FakeCelery:
    """Celery falso para ambiente serverless."""
    def __init__(self, *args, **kwargs):
        self.conf = {"beat_schedule": {}}

    def task(self, *args, **kwargs):
        def decorator(func):
            name = kwargs.get("name", func.__name__)
            return FakeCeleryTask(func, name)
        if args and callable(args[0]):
            return FakeCeleryTask(args[0], args[0].__name__)
        return decorator

    def send_task(self, *args, **kwargs):
        logger.info(f"[CELERY-STUB] send_task: {args}")
        return {"task_id": "stub-task"}


celery_app = FakeCelery("motordebusca")
