from celery.result import result_from_tuple
from contextlib import suppress
from json import dumps, loads

from services.redis_configuration import get_redis_connection
from services.task import TaskService


class RefreshService(object):
    def __init__(self):
        self.task_service = TaskService()

    def is_refreshing(self, ownerid):
        redis = get_redis_connection()
        data_task = redis.hget("refresh", ownerid)
        if not data_task:
            return False
        with suppress(ValueError, TypeError):
            result = result_from_tuple(loads(data_task))
            if not result.ready():
                return True
        redis.hdel("refresh", ownerid)
        return False

    def trigger_refresh(
        self,
        ownerid,
        username,
        sync_teams=True,
        sync_repos=True,
        using_integration=False,
    ):
        if self.is_refreshing(ownerid):
            return
        resp = self.task_service.refresh(
            ownerid, username, sync_repos, sync_teams, using_integration
        )
        # store in redis the task data to be used for `is_refreshing` logic
        redis = get_redis_connection()
        redis.hset("refresh", ownerid, dumps(resp.as_tuple()))
