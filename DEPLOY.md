# Руководство по развертыванию Tabletnica

## Процесс сборки

### 1. Подготовка окружения

Убедитесь, что установлены:

- Node.js (версия 18 или выше)
- npm или yarn

### 2. Установка зависимостей

```bash
# Установка зависимостей
npm install
```

### 3. Настройка переменных окружения

Создайте файл `.env.production` с настройками для продакшн окружения:

```bash
VITE_API_BASE_URL=http://217.174.105.116:8000/
```

Или используйте существующий файл `.env.production`.

### 4. Сборка проекта

```bash
# Сборка фронтенда для продакшн
npm run build
```

Этот скрипт:

1. Проверяет TypeScript типы (`tsc`)
2. Собирает проект с помощью Vite (`vite build`)
3. Создает оптимизированную версию в папке `dist/`

### 5. Проверка сборки

```bash
# Предпросмотр собранного проекта
npm run preview
```

Откройте браузер и перейдите на `http://localhost:4173` для проверки.

## Развертывание на сервер

### Вариант 1: Развертывание с Nginx

#### Шаг 1: Подготовка сервера

1. Установите Nginx на сервер:

```bash
sudo apt update
sudo apt install nginx
```

2. Создайте директорию для приложения:

```bash
sudo mkdir -p /var/www/tabletnica
sudo chown -R $USER:$USER /var/www/tabletnica
```

#### Шаг 2: Загрузка файлов

1. Соберите проект локально:

```bash
npm run build
```

2. Загрузите содержимое папки `dist/` на сервер:

```bash
# Используя scp
scp -r dist/* user@your-server.com:/var/www/tabletnica/

# Или используя rsync
rsync -avz dist/ user@your-server.com:/var/www/tabletnica/
```

#### Шаг 3: Настройка Nginx

1. Скопируйте конфигурацию Nginx:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/tabletnica
```

2. Отредактируйте конфигурацию, заменив `your-domain.com` на ваш домен:

```bash
sudo nano /etc/nginx/sites-available/tabletnica
```

3. Создайте символическую ссылку:

```bash
sudo ln -s /etc/nginx/sites-available/tabletnica /etc/nginx/sites-enabled/
```

4. Проверьте конфигурацию:

```bash
sudo nginx -t
```

5. Перезапустите Nginx:

```bash
sudo systemctl restart nginx
```

#### Шаг 4: Настройка SSL (опционально, но рекомендуется)

1. Установите Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
```

2. Получите SSL сертификат:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. Certbot автоматически обновит конфигурацию Nginx для HTTPS.

### Вариант 2: Развертывание на статический хостинг

#### Netlify

1. Установите Netlify CLI:

```bash
npm install -g netlify-cli
```

2. Соберите проект:

```bash
npm run build
```

3. Деплой:

```bash
netlify deploy --prod --dir=dist
```

4. Настройте переменные окружения в панели Netlify:
   - `VITE_API_BASE_URL` = `http://217.174.105.116:8000/`

#### Vercel

1. Установите Vercel CLI:

```bash
npm install -g vercel
```

2. Деплой:

```bash
vercel --prod
```

3. Настройте переменные окружения в панели Vercel.

#### GitHub Pages

1. Установите `gh-pages`:

```bash
npm install --save-dev gh-pages
```

2. Добавьте скрипт в `package.json`:

```json
"deploy": "npm run build && gh-pages -d dist"
```

3. Деплой:

```bash
npm run deploy
```

**Важно:** Для GitHub Pages нужно настроить `base` в `vite.config.ts`:

```typescript
base: '/your-repo-name/',
```

## Настройка API

Приложение использует внешний API по адресу `http://217.174.105.116:8000/`.

Если нужно изменить адрес API:

1. Обновите `VITE_API_BASE_URL` в `.env.production`
2. Пересоберите проект: `npm run build`
3. Убедитесь, что API сервер доступен и поддерживает CORS для вашего домена

## Проверка после развертывания

1. Откройте сайт в браузере
2. Проверьте консоль браузера на наличие ошибок
3. Проверьте работу API запросов в Network вкладке DevTools
4. Убедитесь, что все страницы загружаются корректно

## Обновление приложения

1. Внесите изменения в код
2. Соберите проект: `npm run build`
3. Загрузите новую версию на сервер:

```bash
rsync -avz dist/ user@your-server.com:/var/www/tabletnica/
```

4. Очистите кеш браузера или используйте версионирование файлов (Vite делает это автоматически)

## Мониторинг и логи

### Nginx логи

```bash
# Логи доступа
sudo tail -f /var/log/nginx/tabletnica_access.log

# Логи ошибок
sudo tail -f /var/log/nginx/tabletnica_error.log
```

### Проверка статуса Nginx

```bash
sudo systemctl status nginx
```

## Устранение неполадок

### Проблема: Белая страница после деплоя

**Решение:**

- Проверьте, что все файлы загружены в правильную директорию
- Проверьте конфигурацию Nginx (особенно `root` и `try_files`)
- Проверьте консоль браузера на наличие ошибок

### Проблема: API запросы не работают

**Решение:**

- Проверьте настройки прокси в Nginx
- Убедитесь, что API сервер доступен и работает по адресу `http://217.174.105.116:8000/`
- Проверьте CORS настройки на API сервере
- Проверьте переменную окружения `VITE_API_BASE_URL`

### Проблема: Роутинг не работает (404 на прямых ссылках)

**Решение:**

- Убедитесь, что в Nginx конфигурации есть `try_files $uri $uri/ /index.html;`
- Проверьте, что `base` в `vite.config.ts` настроен правильно

## Оптимизация производительности

Собранное приложение уже оптимизировано:

- Минификация кода
- Удаление console.log и debugger
- Code splitting (разделение на чанки)
- Gzip сжатие (настроено в Nginx)
- Кеширование статических файлов

## Безопасность

1. **HTTPS:** Настройте SSL сертификат для безопасного соединения
2. **Заголовки безопасности:** Уже настроены в Nginx конфигурации
3. **CORS:** Убедитесь, что API сервер правильно настроен для работы с вашим доменом
