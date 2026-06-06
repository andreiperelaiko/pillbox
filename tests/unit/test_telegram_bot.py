from unittest.mock import MagicMock, patch

from src.telegram_bot import TelegramBot


@patch("src.telegram_bot.save_telegram_chat_id")
@patch("src.telegram_bot.get_user_by_telegram")
@patch.object(TelegramBot, "send_message")
@patch.object(TelegramBot, "get_updates")
def test_process_updates_accepts_start_deep_link(
    mock_get_updates,
    mock_send_message,
    mock_get_user,
    mock_save_chat,
):
    mock_get_updates.side_effect = [
        {
            "ok": True,
            "result": [
                {
                    "update_id": 1,
                    "message": {
                        "text": "/start link",
                        "from": {"username": "doraty228"},
                        "chat": {"id": 12345},
                    },
                }
            ],
        },
        {"ok": True, "result": []},
    ]
    mock_get_user.return_value = {"id": 6, "name": "User", "email": "a@b.c"}

    results = TelegramBot(token="test-token").process_updates()

    assert results[0]["status"] == "linked"
    mock_save_chat.assert_called_once_with(6, "12345")
