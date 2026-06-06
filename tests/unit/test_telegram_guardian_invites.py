from unittest.mock import patch

from src.telegram_bot import TelegramBot


@patch("src.telegram_bot.mark_guardian_invite_party_notified")
@patch("src.telegram_bot.get_guardian_invites_to_notify")
@patch.object(TelegramBot, "send_message", return_value={"ok": True})
def test_process_guardian_invites_guardian_initiated(
    mock_send,
    mock_pending,
    mock_mark,
):
    mock_pending.return_value = [{
        "id": 7,
        "patient_name": "Пациент",
        "guardian_name": "Опекун",
        "relationship": "сын",
        "initiated_by": "guardian",
        "guardian_chat_id": "111",
        "patient_chat_id": "222",
        "guardian_telegram_notified": False,
        "patient_telegram_notified": False,
    }]

    results = TelegramBot(token="test-token").process_guardian_invites()

    assert len(results) == 2
    guardian_call = mock_send.call_args_list[0]
    patient_call = mock_send.call_args_list[1]
    assert guardian_call.kwargs.get("reply_markup") is None
    assert "Ожидаем подтверждения подопечного" in guardian_call.args[1]
    assert "inline_keyboard" in patient_call.kwargs["reply_markup"]
    assert "Подтвердите или отклоните" in patient_call.args[1]


@patch("src.telegram_bot.mark_guardian_invite_party_notified")
@patch("src.telegram_bot.get_guardian_invites_to_notify")
@patch.object(TelegramBot, "send_message", return_value={"ok": True})
def test_process_guardian_invites_patient_initiated(
    mock_send,
    mock_pending,
    mock_mark,
):
    mock_pending.return_value = [{
        "id": 8,
        "patient_name": "Пациент",
        "guardian_name": "Опекун",
        "relationship": "дочь",
        "initiated_by": "patient",
        "guardian_chat_id": "111",
        "patient_chat_id": "222",
        "guardian_telegram_notified": False,
        "patient_telegram_notified": False,
    }]

    results = TelegramBot(token="test-token").process_guardian_invites()

    assert len(results) == 2
    guardian_call = mock_send.call_args_list[0]
    patient_call = mock_send.call_args_list[1]
    assert "inline_keyboard" in guardian_call.kwargs["reply_markup"]
    assert "Подтвердите или отклоните" in guardian_call.args[1]
    assert patient_call.kwargs.get("reply_markup") is None
    assert "Ожидаем подтверждения опекуна" in patient_call.args[1]


@patch.object(TelegramBot, "send_message", return_value={"ok": True})
@patch.object(TelegramBot, "answer_callback_query", return_value={"ok": True})
@patch("src.telegram_bot.respond_to_guardian_invite", return_value="completed")
@patch("src.telegram_bot.get_guardian_invite")
@patch("src.telegram_bot.get_user_by_telegram")
def test_completed_notifies_both_parties(
    mock_get_user,
    mock_get_invite,
    mock_respond,
    mock_answer,
    mock_send,
):
    mock_get_user.return_value = {"id": 2, "name": "Опекун"}
    mock_get_invite.return_value = {
        "patient_name": "Пациент",
        "guardian_name": "Опекун",
        "patient_chat_id": "222",
        "guardian_chat_id": "111",
    }

    result = TelegramBot(token="test-token")._handle_callback({
        "id": "cb1",
        "data": "gi:ok:7",
        "from": {"username": "guardian_user"},
        "message": {"chat": {"id": 111}},
    })

    assert result["status"] == "completed"
    assert mock_send.call_count == 2
    assert all("Опекунство установлено" in call.args[1] for call in mock_send.call_args_list)


@patch.object(TelegramBot, "answer_callback_query", return_value={"ok": True})
@patch("src.telegram_bot.respond_to_guardian_invite", return_value="not_approver")
@patch("src.telegram_bot.get_user_by_telegram")
def test_initiator_callback_rejected(
    mock_get_user,
    mock_respond,
    mock_answer,
):
    mock_get_user.return_value = {"id": 2, "name": "Опекун"}

    result = TelegramBot(token="test-token")._handle_callback({
        "id": "cb1",
        "data": "gi:ok:7",
        "from": {"username": "guardian_user"},
        "message": {"chat": {"id": 111}},
    })

    assert result["status"] == "not_approver"
    mock_answer.assert_called_once()
    assert "другой участник" in mock_answer.call_args[0][1]
