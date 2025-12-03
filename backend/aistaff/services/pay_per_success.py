from functools import wraps
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date
from accounts.models import AIAssistantTask, InsufficientCredits, CreditTransaction
from aistaff.models import AIAgent, AIAgentActionCost


def pay_per_success(task_type=None, cost=None):
    """
    Decorator enforcing pay-per-success with dynamic per-agent pricing.
    Handles reservation, confirmation, and refund automatically.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            user = getattr(self, "staff", None)
            if not user or not hasattr(user, "wallet"):
                return {"error": "User has no wallet"}
            
            wallet = user.wallet
            agent_name = self.__class__.__name__
            action_name = task_type or func.__name__

            # --- Determine dynamic cost ---
            effective_cost = Decimal(str(_get_dynamic_cost(agent_name, action_name, cost)))
            # --- Create task record ---
            task = AIAssistantTask.objects.create(
                user=user,
                task_type=action_name,
                agent=agent_name,
                reserved_amount=effective_cost,
                status="pending",
            )

            # --- Reserve credits before running the AI action ---
            try:
                tx = reserve_for_task(wallet, effective_cost, task, agent_name)
            except InsufficientCredits:
                _mark_task_failed(task, "Insufficient credits")
                return {"error": "Insufficient credits"}
            except Exception as e:
                _mark_task_failed(task, str(e))
                return {"error": str(e)}

            # --- Execute the real AI function ---
            try:
                result = func(self, *args, **kwargs)
                result = _clean_json(result)  # ✅ Sanitize result before saving
                success = _is_success(result)

                if success:
                    mark_success(wallet, tx, task, result)
                else:
                    reason = result.get("error", "Task failed") if isinstance(result, dict) else "Task failed"
                    mark_failed(wallet, tx, task, reason=reason)
                return result

            except Exception as e:
                mark_failed(wallet, tx, task, reason=str(e))
                return {"error": str(e)}

        return wrapper
    return decorator


# -------------------------------------------------
# 🧩 Wallet + Transaction Logic
# -------------------------------------------------

def reserve_for_task(wallet, amount, task, agent_name):
    """Temporarily reserve credits for a pending AI task."""
    if wallet.total_credits < amount:
        raise InsufficientCredits("Insufficient credits")

    with transaction.atomic():
        wallet.reserved_credits += amount
        wallet.save(update_fields=["reserved_credits"])

        tx = CreditTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            type="reserve",
            status="pending",
            AI_staff=agent_name,   # ✅ Use agent name string
            task=task,    # ✅ FK to AIAssistantTask
            meta={"reason": "reserve_for_task"},
        )
    return tx


def refund_reservation(wallet, tx):
    """Refund reserved credits when a task fails or is cancelled."""
    with transaction.atomic():
        wallet.reserved_credits = max(wallet.reserved_credits - tx.amount, Decimal("0"))
        wallet.save(update_fields=["reserved_credits"])

        tx.status = "refund"
        tx.meta["reason"] = "refund_reservation"
        tx.meta = _clean_json(tx.meta)
        tx.save(update_fields=["status", "meta"])
    return tx


def confirm_reservation(wallet, tx):
    """Deduct reserved credits permanently when task succeeds."""
    with transaction.atomic():
        if wallet.reserved_credits < tx.amount:
            raise ValueError("Reserved credit mismatch")

        wallet.reserved_credits -= tx.amount
        wallet.total_credits -= tx.amount
        wallet.save(update_fields=["reserved_credits", "total_credits"])

        tx.status = "confirmed"
        tx.type = "deduct"
        tx.meta["reason"] = "deducted_reservation_credits"
        tx.meta = _clean_json(tx.meta)
        tx.save(update_fields=["status", "type", "meta"])
    return tx


# -------------------------------------------------
# ✅ Mark Success / Failure
# -------------------------------------------------

def mark_success(wallet, tx, task, result=None):
    """Mark task success and confirm credit deduction."""
    confirm_reservation(wallet, tx)
    _mark_task_success(task, result)
    return True


def mark_failed(wallet, tx, task, reason=""):
    """Mark task failure and refund reserved credits."""
    refund_reservation(wallet, tx)
    _mark_task_failed(task, reason)
    return False


# -------------------------------------------------
# 🧠 Task Helpers
# -------------------------------------------------

def _mark_task_success(task, meta=None):
    task.status = "success"
    task.result = _clean_json(meta or {})
    task.failed_reason = ""
    task.updated_at = timezone.now()
    task.save(update_fields=["status", "result", "failed_reason", "updated_at"])


def _mark_task_failed(task, reason=""):
    task.status = "failed"
    task.failed_reason = str(reason)
    task.updated_at = timezone.now()
    task.save(update_fields=["status", "failed_reason", "updated_at"])


# -------------------------------------------------
# 💰 Dynamic Credit Cost Lookup
# -------------------------------------------------

def _get_dynamic_cost(agent_key, action_key, fallback_cost=1.0):
    """Dynamic lookup for agent & action cost."""
    try:
        agent = AIAgent.objects.filter(agent=agent_key, is_active=True).first()
       
        if not agent:
            agent =AIAgent.objects.filter(agent="*", is_active=True).first()
        if agent:
            rec = (
                AIAgentActionCost.objects.filter(agent_key=agent, action_key=action_key, is_active=True).first()
                or AIAgentActionCost.objects.filter(agent_key="*", action_key=action_key, is_active=True).first()
            )
            if rec:
                return float(rec.cost)
    except Exception:
        pass
    return fallback_cost


# -------------------------------------------------
# 🧩 Success Detection Logic
# -------------------------------------------------

def _is_success(result):
    if isinstance(result, dict):
        if result.get("status") == "success":
            return True
        if "text" in result and not result.get("error"):
            return True
    return False


# -------------------------------------------------
# 🧹 Utility — Clean JSON before saving
# -------------------------------------------------

def _clean_json(data):
    """
    Convert non-serializable data (datetime, Decimal, etc.) into JSON-safe types.
    """
    if data is None:
        return None
    if isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    if isinstance(data, dict):
        return {k: _clean_json(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_clean_json(v) for v in data]
    return str(data)
