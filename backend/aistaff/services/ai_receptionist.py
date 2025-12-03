from openai import OpenAI
from django.conf import settings
import json
from workspace.models import RoomBooking, Room, SupportTicket
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from aistaff.services.pay_per_success import pay_per_success
from django.utils import timezone
from django.core.mail import send_mail

client = "OpenAI(api_key=settings.OPENAI_API_KEY)"


class AIReceptionist:
    def __init__(self, org, city, staff_user=None, faqs=None, bookings=None, session=None):
        self.org = org
        self.city = city
        self.staff = staff_user
        self.faqs = faqs or {}
        self.bookings = bookings or {}
        self.session = session or {}

    # ---------------- CONTEXT ----------------
    def build_context(self):
        remembered = ""
        if self.session.get("visitor_name") or self.session.get("visitor_email"):
            remembered = f"""
            The visitor has already introduced themselves:
            Name: {self.session.get("visitor_name")}
            Email: {self.session.get("visitor_email")}
            """
        return f"""
        You are the receptionist for {self.org['name']} in {self.city}.
        
        Your responsibilities:
        - Greet visitors politely and warmly.
        - Answer FAQs: {json.dumps(self.faqs)}.
        - Provide details about the organization: {self.org.get('details', '')}.
        - Follow booking rules: {json.dumps(self.bookings)}.
        - If visitor shares their name/email, remember it for later.
        - If visitor asks about their previous bookings, check the database.
        - If you asked the visitor for clarification earlier, wait for their follow-up reply.

        {remembered}

        JSON-only actions:
        - Book a room → "action": "book_room"
        - Recall bookings → "action": "recall_bookings"
        - Cancel booking → "action": "cancel_booking"
        - Reschedule booking → "action": "reschedule_booking"
        - Escalate → "action": "escalate"

        Otherwise, reply in plain text.
        """

    # ---------------- RESPOND ----------------
    def respond(self, message: str):
        # Check if user is clarifying a previous step
        if self.session.get("pending_action"):
            return self.handle_followup(message)

        context = self.build_context()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
        )
        reply = resp.choices[0].message.content.strip()

        # Detect JSON actions
        if reply.startswith("{") and "action" in reply:
            try:
                data = json.loads(reply)
                action = data.get("action")

                if action == "book_room":
                    if data.get("visitor_name"):
                        self.session["visitor_name"] = data["visitor_name"]
                    if data.get("visitor_email"):
                        self.session["visitor_email"] = data["visitor_email"]
                    return self.handle_booking(data)

                elif action == "recall_bookings":
                    return self.recall_bookings()

                elif action == "cancel_booking":
                    return self.cancel_booking(data)

                elif action == "reschedule_booking":
                    return self.reschedule_booking(data)

                elif action == "escalate":
                    return "👩‍💼 I’ll connect you with a staff member right away."

            except Exception as e:
                return f"⚠️ Error interpreting request: {str(e)}"

        # Detect "my name is ..." / "email ..."
        self.detect_and_remember_visitor(message)
        return reply

    # ---------------- FOLLOW-UP HANDLER ----------------
    def handle_followup(self, message: str):
        pending = self.session.pop("pending_action")
        options = self.session.pop("pending_options", [])

        chosen = None
        msg_lower = message.lower()

        for opt in options:
            if opt["time"].lower() in msg_lower or opt["room"].lower() in msg_lower:
                chosen = opt
                break

        if not chosen:
            return "⚠️ Sorry, I couldn’t match that to any of your bookings. Please specify again."

        if pending == "cancel":
            return self._finalize_cancel(chosen["booking_id"])
        elif pending == "reschedule":
            # Here we’d need new times (can prompt again or expect them in message)
            return f"ℹ️ You selected {chosen['room']} at {chosen['time']} to reschedule. Please tell me the new date/time."

    # ---------------- MEMORY HELPERS ----------------
    def detect_and_remember_visitor(self, message: str):
        msg = message.lower()
        if "name is" in msg:
            name = message.split("name is")[-1].strip().split()[0:3]
            self.session["visitor_name"] = " ".join(name)
        if "email" in msg and "@" in msg:
            email = [word for word in message.split() if "@" in word]
            if email:
                self.session["visitor_email"] = email[0]

    # ---------------- BOOKINGS ----------------
    @pay_per_success(task_type="book_room")
    def handle_booking(self, data):
        try:
            room = Room.objects.get(name=data["room"])
        except Room.DoesNotExist:
            return f"❌ Sorry, I couldn’t find the room '{data['room']}'."

        start_time = parse_datetime(data["start_time"])
        end_time = parse_datetime(data["end_time"])

        if not start_time or not end_time:
            return "⚠️ Invalid date/time. Please try again."
        if start_time < now():
            return "⚠️ You cannot book a room in the past."

        conflict = RoomBooking.objects.filter(
            room=room,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        if conflict:
            return f"❌ Sorry, {room.name} is already booked at that time."

        booking = RoomBooking.objects.create(
            room=room,
            visitor_name=data.get("visitor_name", self.session.get("visitor_name", "Guest")),
            visitor_email=data.get("visitor_email", self.session.get("visitor_email", "unknown@example.com")),
            start_time=start_time,
            end_time=end_time,
            confirmed=True,
        )
        return{"status": "success", "message": f"✅ Booking confirmed: {booking.room.name} on {start_time.strftime('%Y-%m-%d %H:%M')}.", "booking_id": booking.id}
    
    # -------------------------------------------------
    # 🕒 RESCHEDULE BOOKING
    # -------------------------------------------------
    @pay_per_success(task_type="reschedule_booking")
    def reschedule_booking(self, data):
        visitor_email = self.session.get("visitor_email")
        if not visitor_email:
            return {"status": "failed", "error": "Please provide your email to find your bookings."}

        # Get old booking date
        old_start = parse_datetime(data.get("old_start_time"))
        if not old_start:
            return {"status": "failed", "error": "Invalid or missing old booking date/time."}

        # Find existing booking
        try:
            booking = RoomBooking.objects.get(visitor_email=visitor_email, start_time=old_start)
        except RoomBooking.DoesNotExist:
            return {"status": "failed", "error": "No booking found for that time."}

        # Get new start and end
        new_start = parse_datetime(data.get("new_start_time"))
        new_end = parse_datetime(data.get("new_end_time"))
        if not new_start or not new_end:
            return {"status": "failed", "error": "Please provide both new start and end times."}
        if new_start < now():
            return {"status": "failed", "error": "You cannot reschedule to a past time."}

        # Check conflicts
        conflict = RoomBooking.objects.filter(
            room=booking.room,
            start_time__lt=new_end,
            end_time__gt=new_start
        ).exclude(id=booking.id).exists()
        if conflict:
            return {"status": "failed", "error": f"{booking.room.name} is already booked at that time."}

        # Update booking
        booking.start_time = new_start
        booking.end_time = new_end
        booking.save(update_fields=["start_time", "end_time"])

        return {
            "status": "success",
            "message": f"✅ Booking rescheduled: {booking.room.name} now on {new_start.strftime('%Y-%m-%d %H:%M')}.",
            "booking_id": booking.id,
        }

    
    @pay_per_success(task_type="recall_bookings")
    def recall_bookings(self):
        visitor_email = self.session.get("visitor_email")
        visitor_name = self.session.get("visitor_name")

        if not visitor_email and not visitor_name:
            return "ℹ️ Please tell me your email so I can find your bookings."

        qs = RoomBooking.objects.all()
        if visitor_email:
            qs = qs.filter(visitor_email=visitor_email)
        elif visitor_name:
            qs = qs.filter(visitor_name__icontains=visitor_name)

        bookings = qs.order_by("start_time")
        if not bookings.exists():
            return "ℹ️ No past bookings found."

        response = ["📅 Your booking history:"]
        for b in bookings:
            response.append(f"- {b.room.name} | {b.start_time.strftime('%Y-%m-%d %H:%M')}")
            result = "\n".join(response)
        return {"status": "success", "message": result,}
    

    @pay_per_success(task_type="escalate_booking")
    def escalate(self, data=None):
        """
        Escalate the conversation to a human receptionist/staff.
        Creates a SupportTicket record for tracking.
        """
        user = getattr(self, "staff", None)
        if not user:
            return {"status": "failed", "error": "No authenticated user found."}

        visitor_name = self.session.get("visitor_name", "Guest")
        visitor_email = self.session.get("visitor_email", "unknown@example.com")

        # Extract optional details from the AI or user message
        issue_details = ""
        if data:
            if isinstance(data, dict):
                issue_details = data.get("message") or data.get("issue") or ""
            else:
                issue_details = str(data)

        # Create the support ticket
        ticket = SupportTicket.objects.create(
            user=user,
            subject=f"Escalation Request from {visitor_name}",
            message=f"""
              Visitor Name: {visitor_name}
              Visitor Email: {visitor_email}
              Issue: {issue_details or 'N/A'}
              Created: {timezone.now().strftime('%Y-%m-%d %H:%M')}
              """.strip(),
            status="open",
        )

        # Optionally notify staff (e.g., via email or Slack)
        send_mail(
             subject=f"[AI Escalation] New ticket from {visitor_name}",
             message=ticket.message,
             from_email="noreply@yourapp.com",
             recipient_list=["support@yourcompany.com"],
         )

        return {
            "status": "success",
            "message": f"🙋 Escalation logged. Ticket #{ticket.id} created for human follow-up.",
            "ticket_id": ticket.id,
        }

    
    @pay_per_success(task_type="cancel_booking")
    def cancel_booking(self, data):
        visitor_email = self.session.get("visitor_email")
        if not visitor_email:
            return "ℹ️ Please provide your email to find your bookings."

        booking_date = parse_datetime(data.get("booking_date"))
        if not booking_date:
            return "⚠️ Invalid date. Please specify the booking time."

        qs = RoomBooking.objects.filter(
            visitor_email=visitor_email,
            start_time__date=booking_date.date()
        )
        if not qs.exists():
            return "⚠️ No booking found for that date."

        if qs.count() > 1:
            options = []
            for b in qs:
                options.append({
                    "booking_id": b.id,
                    "room": b.room.name,
                    "time": b.start_time.strftime("%H:%M"),
                })
            self.session["pending_action"] = "cancel"
            self.session["pending_options"] = options
            return (
                "🤔 You have multiple bookings on that day. Which one should I cancel?\n" +
                "\n".join([f"- {o['room']} at {o['time']}" for o in options])
            )

        booking = qs.first()
        return self._finalize_cancel(booking.id)

    def _finalize_cancel(self, booking_id):
        try:
            booking = RoomBooking.objects.get(id=booking_id)
        except RoomBooking.DoesNotExist:
            return "⚠️ Booking no longer exists."
        booking.delete()
        return{"status": "success", "message": f"✅ Your booking for {booking.room.name} at {booking.start_time.strftime('%Y-%m-%d %H:%M')} has been cancelled."}
