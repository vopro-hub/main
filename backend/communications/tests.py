from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock

from communications.models import CommunicationLog, SMSMessage, EmailMessage
from communications.tasks import classify_and_autoreply


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class TestClassifyAndAutoReply(TestCase):
    def setUp(self):
        # --- Create inbound SMS ---
        self.sms_log = CommunicationLog.objects.create(
            type="sms",
            direction="inbound",
            status="received",
        )
        SMSMessage.objects.create(
            log=self.sms_log,
            from_number="+15550001111",
            body="Hi, I need to book a meeting for tomorrow.",
        )

        # --- Create inbound Email ---
        self.email_log = CommunicationLog.objects.create(
            type="email",
            direction="inbound",
            status="received",
        )
        EmailMessage.objects.create(
            log=self.email_log,
            from_email="client@example.com",
            subject="Request for report",
            body_text="Can you send me the daily sales report?",
        )

    # ✅ Test 1 — SMS auto-reply
    @patch("communications.tasks.send_sms_task.delay")
    @patch("communications.tasks.AIOfficeAssistant")
    def test_sms_auto_reply_creates_outbound_log_and_calls_twilio(
        self, mock_ai_class, mock_send_sms
    ):
        mock_ai_instance = MagicMock()
        mock_ai_instance.classify_or_reply.return_value = {
            "action": "reply_sms",
            "text": "Sure! I've booked that meeting for you.",
        }
        mock_ai_class.return_value = mock_ai_instance

        classify_and_autoreply(self.sms_log.id)

        # AI called with extracted SMS text
        mock_ai_instance.classify_or_reply.assert_called_once_with(
            "Hi, I need to book a meeting for tomorrow."
        )

        # Outbound SMS log created
        outbound = CommunicationLog.objects.filter(direction="outbound", type="sms").first()
        self.assertIsNotNone(outbound, "No outbound SMS log created")
        self.assertIn("booked that meeting", outbound.payload.get("text", ""))

        # Twilio task enqueued
        mock_send_sms.assert_called_once()

    # ✅ Test 2 — Email auto-reply
    @patch("communications.tasks.send_email_task.delay")
    @patch("communications.tasks.AIOfficeAssistant")
    def test_email_auto_reply_creates_outbound_log_and_calls_smtp(
        self, mock_ai_class, mock_send_email
    ):
        mock_ai_instance = MagicMock()
        mock_ai_instance.classify_or_reply.return_value = {
            "action": "reply_email",
            "text": "Attached is your sales report for today.",
        }
        mock_ai_class.return_value = mock_ai_instance

        classify_and_autoreply(self.email_log.id)

        mock_ai_instance.classify_or_reply.assert_called_once_with(
            "Can you send me the daily sales report?"
        )

        # Outbound email log created
        outbound = CommunicationLog.objects.filter(direction="outbound", type="email").first()
        self.assertTrue(outbound, "No outbound Email log created")
        self.assertIn("sales report", outbound.payload.get("text", ""))

        # SMTP send task called
        mock_send_email.assert_called_once()

    # ✅ Test 3 — Empty message does not trigger AI
    @patch("communications.tasks.AIOfficeAssistant")
    def test_empty_message_does_not_trigger_ai(self, mock_ai_class):
        empty_log = CommunicationLog.objects.create(
            type="sms",
            direction="inbound",
            status="received",
        )
        # No SMSMessage created → no text extracted
        classify_and_autoreply(empty_log.id)

        # AI should never be called
        mock_ai_class.assert_not_called()

    # ✅ Test 4 — Unknown action handled gracefully
    @patch("communications.tasks.send_sms_task.delay")
    @patch("communications.tasks.send_email_task.delay")
    @patch("communications.tasks.AIOfficeAssistant")
    def test_ai_handles_unknown_action_gracefully(
        self, mock_ai_class, mock_send_email, mock_send_sms
    ):
        mock_ai_instance = MagicMock()
        mock_ai_instance.classify_or_reply.return_value = {
            "action": "unknown",
            "text": "I'm not sure what to do.",
        }
        mock_ai_class.return_value = mock_ai_instance

        classify_and_autoreply(self.sms_log.id)

        # Should call AI but not create outbound logs or send anything
        mock_ai_instance.classify_or_reply.assert_called_once()
        self.assertFalse(
            CommunicationLog.objects.filter(direction="outbound").exists(),
            "Unexpected outbound message was created.",
        )

        mock_send_sms.assert_not_called()
        mock_send_email.assert_not_called()
