import json
from django.conf import settings
from django.utils.dateparse import parse_datetime
from datetime import datetime
from openai import OpenAI
import requests
from aistaff.models import Task, Meeting, Note, Resource, FileRecord, EmailDraft, AssistantLog, AssistantActionType, AssistantActionSubtype
from aistaff.services.pay_per_success import pay_per_success
from django.contrib.auth import get_user_model

User = get_user_model()

client = "OpenAI(api_key=settings.OPENAI_API_KEY)"
 
#def safe_json(obj):
#    def default(o):
#        if isinstance(o, (datetime)):
#            return o.isoformat()
#        raise TypeError(f"object of type {o.__class__.__name__} is not JSON serializable")
#    return json.loads(json.dumps(obj, default=default))

    

class AIOfficeAssistant:
    
    def __init__(self, org: dict, staff_user=None, session=None):
        self.org = org or {}
        self.staff = staff_user
        self.session = session or {}  # Django session
            
    def build_context(self):
        return (
            f"You are an office assistant for {self.org.get('name','the organization')}.\n"
            "You may return plain text replies or a JSON action. When returning a JSON action the top-level "
            "object must contain an 'action' field. Supported actions: create_task, list_tasks, schedule_meeting, get_agenda, "
            "draft_email, file_search, resource_check, note_taking, recall_notes, cancel_task, cancel_meeting, reschedule_meeting.\n"
            "When providing dates use ISO 8601 (YYYY-MM-DDTHH:MM:SS)."
        )
    
    def respond(self, message: str):
        system = self.build_context()
        reply, parsed = None, {}
        action_type, subtype = None, None
        out = {}
        action = None

        try:
            if "meeting" in message.lower():
                action = "schedule_meeting"
                data = {
                    "action": "schedule_meeting",
                    "topic": "AI Meeting",
                    "start_time": datetime.now(),
                }
                out = self.action_schedule_meeting(data)
                reply = out.get("text", "Meeting booked successfully.")
                action_type, subtype = self.infer_type_and_subtype({"action": action})
            elif "task" in message.lower():
                action = "create_task"
                data = {
                    "action": "create_task",
                    "title": "Follow up with client",
                    "description": "Call client",
                    "due_date": datetime.now(),
                }
                out = self.action_create_task(data)
                reply = out.get("text", "Created successfully.")
                action_type, subtype = self.infer_type_and_subtype({"action": action})
            else:
                reply ="This is a simulated AI Assistant."
                out = {"text": reply}
                action_type, subtype = self.infer_type_and_subtype({"action": "general"})
            #resp = client.chat.completions.create(
            #    model="gpt-4o-mini",
            #    messages=[
            #        {"role": "system", "content": system},
            #        {"role": "user", "content": message}
            #    ],
            #    max_tokens=700,
            #)
            #reply = resp.choices[0].message["content"].strip()
        except Exception as e:
            reply = f"LLM error: {e}"

        if reply and (reply.startswith("{") or reply.startswith("[")):
            try:
                parsed = json.loads(reply)
                if isinstance(parsed, dict) and parsed.get("action"):
                    out = self.handle_action(parsed)
                    action_type, subtype = self.infer_type_and_subtype(parsed)
                else:
                    out = {"text": reply}
            except Exception:
                out = {"text": reply}
        else:
            out = {"text": reply}

        # --- Save log ---
        AssistantLog.objects.create(
            user=self.staff,
            input_text=message,
            response_text=out.get("text") or reply or "",
            action_data= action, # For testing only
            #action_data=parsed if isinstance(parsed, dict) else {},
            #type=action_type,
            #subtype=subtype,
        )

        return out

    def infer_type_and_subtype(self, parsed: dict):
        """Map action to normalized type/subtype in DB"""
        action = parsed.get("action", "")
        main = "general"
        subtype = ""
        if action.startswith("task"):
            main = "task"
            mapping = {
                "task_add": "created",
                "task_update": "updated",
                "task_delete": "deleted",
                "task_complete": "completed",
            }
            subtype = mapping.get(action, "")
    
        elif action.startswith("meeting"):
            main = "meeting"
            mapping = {
                "meeting_schedule": "scheduled",
                "meeting_reschedule": "rescheduled",
                "meeting_cancel": "cancelled",
            }
            subtype = mapping.get(action, "")
    
        elif action.startswith("note"):
            main = "note"
            mapping = {
                "note_add": "created",
                "note_update": "updated",
                "note_delete": "deleted",
            }
            subtype = mapping.get(action, "")
    
        elif action.startswith("resource"):
            main = "resource"
    
        elif action.startswith("file"):
            main = "file"
    
        elif action.startswith("email"):
            main = "email"
            mapping = {
                "email_send": "sent",
                "email_draft": "drafted",
            }
            subtype = mapping.get(action, "")
    
        # 🔗 Normalize against DB
        type_obj, _ = AssistantActionType.objects.get_or_create(
            name=main,
            defaults={"label": main.capitalize()},
        )
        subtype_obj = None
        if subtype:
            subtype_obj, _ = AssistantActionSubtype.objects.get_or_create(
                type=type_obj,
                name=subtype,
                defaults={"label": subtype.capitalize()},
            )
    
        return type_obj, subtype_obj

    def handle_action(self, data: dict):
        action = data.get("action")
        try:
            handler = getattr(self, f"action_{action}", None)
            if not handler:
                return {"text": f"Unknown action: {action}"}
            return handler(data)
        except Exception as e:
            return {"error": "action_failed", "detail": str(e)}

    # ----- Actions -----
    @pay_per_success(task_type="create_task")
    def action_create_task(self, data):
        title = data.get("task_title") or data.get("title")
        due = parse_datetime(data.get("due_date")) if data.get("due_date") else None
        desc = data.get("description") or ""
        t = Task.objects.create(title=title, description=desc, due_date=due, assigned_to=self.staff)
        # persist in session history
        self._add_to_history({"type": "task", "id": t.id})
        return {"text": f"Task created: {t.title}", "task_id": t.id}
    
    @pay_per_success(task_type="list_tasks")
    def action_list_tasks(self, data):
        qs = Task.objects.filter(assigned_to=self.staff).order_by("due_date")
        out = [{"id": t.id, "title": t.title, "due": t.due_date.isoformat() if t.due_date else None, "status": t.status} for t in qs]
        return {"tasks": out}
    
    @pay_per_success(task_type="schedule_meeting")
    def action_schedule_meeting(self, data):
        topic = data.get("topic") or "Meeting"
        start_time = data.get("start_time") or datetime.now() #For testing only
        #start = parse_datetime(data.get("start_time") or data.get("start_time"))
        end_time = parse_datetime(data.get("end_time")) if data.get("end_time") else None
        participants = data.get("participants") or data.get("emails") or "abav@mail"
        meeting = Meeting.objects.create(topic=topic, start_time=start_time, end_time=end_time, participants=participants, created_by=self.staff)
        self._add_to_history({"type": "meeting", "id": meeting.id})
        result = {"status": "success", "meeting": meeting,}
        
        return result
    
    
    @pay_per_success(task_type="get_agenda")
    def action_get_agenda(self, data):
        date = parse_datetime(data.get("date")) if data.get("date") else datetime.now()
        meetings = Meeting.objects.filter(start_time__date=date.date(), created_by=self.staff)
        out = [{"id": m.id, "topic": m.topic, "start": m.start_time.isoformat()} for m in meetings]
        return {"agenda": out}
    
    @pay_per_success(task_type="draft_email")
    def action_draft_email(self, data):
        subject = data.get("subject") or ""
        body = data.get("body") or ""
        to = data.get("to") or []
        draft = EmailDraft.objects.create(subject=subject, body=body, to=list(to), created_by=self.staff)
        self._add_to_history({"type": "email", "id": draft.id})
        return {"text": "Email draft saved.", "draft_id": draft.id}
    
    @pay_per_success(task_type="file_search")
    def action_file_search(self, data):
        q = data.get("keywords") or data.get("query") or ""
        files = FileRecord.objects.filter(title__icontains=q)[:10]
        out = [{"id": f.id, "title": f.title, "url": f.url} for f in files]
        return {"files": out}

    @pay_per_success(task_type="resource_check")
    def action_resource_check(self, data):
        name = data.get("item") or data.get("resource")
        res = Resource.objects.filter(name__icontains=name).first()
        if not res:
            return {"text": f"No resource found for '{name}'."}
        return {"text": f"{res.name}: {res.quantity} in stock.", "resource": {"id": res.id, "quantity": res.quantity}}

    @pay_per_success(task_type="note_taking")
    def action_note_taking(self, data):
        content = data.get("content") or ""
        n = Note.objects.create(content=content, created_by=self.staff)
        self._add_to_history({"type": "note", "id": n.id})
        return {"text": "Note saved.", "note_id": n.id}

    @pay_per_success(task_type="recall_notes")
    def action_recall_notes(self, data):
        keyword = data.get("keyword") or ""
        notes = Note.objects.filter(content__icontains=keyword, created_by=self.staff)[:20]
        return {"notes": [{"id": n.id, "content": n.content} for n in notes]}
    
    @pay_per_success(task_type="cancel_task")
    def action_cancel_task(self, data):
        tid = data.get("task_id")
        t = Task.objects.filter(id=tid, assigned_to=self.staff).first()
        if not t:
            return {"text": "Task not found."}
        t.status = "cancelled"
        t.save()
        return {"text": f"Task '{t.title}' cancelled."}

    @pay_per_success(task_type="cancel_meeting")
    def action_cancel_meeting(self, data):
        mid = data.get("meeting_id")
        m = Meeting.objects.filter(id=mid).first()
        if not m:
            return {"text": "Meeting not found."}
        m.delete()
        return {"text": f"Meeting '{m.topic}' cancelled."}

    @pay_per_success(task_type="reschedule_meeting")
    def action_reschedule_meeting(self, data):
        mid = data.get("meeting_id")
        m = Meeting.objects.filter(id=mid).first()
        if not m:
            return {"text": "Meeting not found."}
        s = parse_datetime(data.get("start_time")) or m.start_time
        e = parse_datetime(data.get("end_time")) if data.get("end_time") else m.end_time
        m.start_time = s
        m.end_time = e
        m.save()
        return {"text": f"Meeting '{m.topic}' rescheduled."}

    # ---- helpers ----
    def _add_to_history(self, entry):
        hist = self.session.get("ai_assistant_history", [])
        hist.append(entry)
        self.session["ai_assistant_history"] = hist
        # mark session changed (if real Django session passed, ensure modified True)
        try:
            self.session.modified = True
        except Exception:
            pass
