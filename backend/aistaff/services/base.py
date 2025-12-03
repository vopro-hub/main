from .pay_per_success import pay_per_success

class AIBaseAgent:
    """
    Base class for all AI staff agents.
    Provides shared Pay-Per-Success behavior globally.
    """
    credits_per_task = 1

    def __init__(self, user, org=None, context=None):
        self.user = user
        self.org = org or {}
        self.context = context or {}

    @pay_per_success(task_type="generic_ai_task", cost=1)
    def perform_task(self, callback):
        """
        Wraps any callable into pay-per-success logic.
        """
        return callback()
