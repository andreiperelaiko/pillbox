from unittest.mock import MagicMock, patch

from src.mailer import Mailer


@patch("src.mailer.smtplib.SMTP")
def test_mailer_send_success(mock_smtp):
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance

    mailer = Mailer(host="localhost", port=1025, from_addr="test@pi11box.ru")
    result = mailer.send("user@test.pi11box", "Тема", "Текст")

    assert result["status"] == "sent"
    smtp_instance.send_message.assert_called_once()


@patch("src.mailer.get_pending_emails", return_value=[
    {"id": 1, "to_email": "a@test.pi11box", "subject": "S", "body": "B"},
])
@patch("src.mailer.mark_email_sent")
@patch.object(Mailer, "send", return_value={"status": "sent", "to": "a@test.pi11box"})
def test_mailer_process_outbox(mock_send, mock_mark, mock_pending):
    results = Mailer().process_outbox()
    assert len(results) == 1
    mock_mark.assert_called_once_with(1)
