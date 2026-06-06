workspace "Pillbox" "C4-архитектура приложения Таблетница" {

    !identifiers hierarchical

    model {
        user = person "Подопечный" "Принимает лекарства; приглашает опекуна; подтверждает запрос в Telegram"
        guardian = person "Опекун" "Следит за приёмами; может запросить опекунство; подтверждает приглашение в Telegram"

        pillbox = softwareSystem "Таблетница" "Напоминания о лекарствах, уведомления опекунам, подтверждение опекунства через @p111boxbot" {
            spa = container "Сайт" "Лекарства, расписание, опекуны, настройки" "React / Vite"
            api = container "Сервер API" "Авторизация, лекарства, опекуны; создаёт guardian_invites" "FastAPI / Python" {
                auth = component "Авторизация" "Регистрация, логин, cookie-сессии" "auth.py"
                routes = component "Маршруты API" "attach/invite опекунов, CRUD лекарств" "api.py"
                dbAccess = component "Работа с БД" "guardian_invites → user_guardians после подтверждения" "db.py"
                auth -> dbAccess "Использует"
                routes -> auth "Проверяет сессию"
                routes -> dbAccess "Использует"
            }
            scheduler = container "Планировщик" "Ищет пропущенные приёмы, до 3 напоминаний" "scheduler.py"
            mailer = container "Почтовик" "Отправляет письма из email_outbox" "mailer.py"
            bot = container "Telegram-бот" "Привязка /start, кнопки опекунства, напоминания" "telegram_bot.py" {
                botCore = component "Логика бота" "Polling, Принять/Отклонить, рассылка" "telegram_bot.py"
                botDb = component "Работа с БД" "Очереди guardian_invites и notifications" "db.py"
                botCore -> botDb "Использует"
            }
            db = container "База данных" "Аккаунты, лекарства, опекунство (invites + guardians), уведомления" "PostgreSQL 16" {
                tags "Database"
            }

            spa -> api "Вызывает" "HTTPS/JSON"
            api -> db "Читает и записывает" "SQL/TCP"
            scheduler -> db "Ищет просроченные приёмы" "SQL/TCP"
            bot -> db "Читает invites и notifications" "SQL/TCP"
            mailer -> db "Читает email_outbox" "SQL/TCP"
        }

        telegram = softwareSystem "Telegram" "Бот @p111boxbot: подтверждение опекунства и напоминания" {
            tags "External"
        }

        user -> pillbox "Использует"
        guardian -> pillbox "Использует"
        user -> telegram "Подтверждает опекунство"
        guardian -> telegram "Читает уведомления и подтверждает"
        pillbox -> telegram "Отправляет сообщения" "HTTPS"

        production = deploymentEnvironment "Production" {
            deploymentNode server "Сервер" "Yandex Cloud VM" "Ubuntu" {
                deploymentNode nginxNode "nginx" "TLS termination, reverse proxy" "nginx"
                deploymentNode apiService "pillbox-api" "FastAPI + uvicorn" "systemd" {
                    containerInstance pillbox.api
                }
                deploymentNode schedulerService "pillbox-scheduler" "Проверка пропущенных приёмов" "systemd" {
                    containerInstance pillbox.scheduler
                }
                deploymentNode mailerService "pillbox-mailer" "Отправка писем" "systemd" {
                    containerInstance pillbox.mailer
                }
                deploymentNode dbService "PostgreSQL" "Хранение данных" "PostgreSQL 16" {
                    containerInstance pillbox.db
                }
                deploymentNode botService "pillbox-telegram-bot" "Telegram polling" "systemd" {
                    containerInstance pillbox.bot
                }
            }
        }
    }

    views {
        systemContext pillbox "SystemContext" {
            title "Контекст системы"
            include *
            autoLayout lr
        }

        container pillbox "Containers" {
            title "Контейнеры"
            include *
            autoLayout tb
        }

        component pillbox.api "ApiComponents" {
            title "Компоненты REST API"
            include *
            autoLayout lr
        }

        component pillbox.bot "BotComponents" {
            title "Компоненты Telegram-бота"
            include *
            autoLayout lr
        }

        deployment pillbox production "ProductionDeployment" {
            title "Продакшен (pi11box.ru)"
            include *
            autoLayout tb
        }

        styles {
            element "Person" {
                shape Person
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Database" {
                shape Cylinder
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }

        theme default
    }

    configuration {
        scope softwaresystem
    }

}
