# Terminal Chat

Простой терминальный чат: сервер на C, клиент на Python с GUI на tkinter.

## Стек технологий

- **Сервер:** C
- **Клиент:** Python 3 (tkinter)
- **Транспорт:** TCP/IP с SSL/TLS-шифрованием
- **Упаковка:** Docker

## Структура проекта

```
terminal_chat/
├── chat_app.py           # Python-клиент с GUI
├── server.c              # Исходник сервера на C
├── Dockerfile            # Сборка образа сервера
├── .dockerignore         # Что не отправлять в контекст сборки
├── server.crt.example    # Пример: как сгенерировать SSL-сертификаты
└── .gitignore
```

## Требования

### Сервер

- **ОС:** Linux (Ubuntu, Debian, Arch и др.)
  - Сервер использует стандартные библиотеки C, POSIX-сокеты и OpenSSL.
  - **Не собирается** на нативном Windows. Для Windows используйте Docker Desktop с WSL 2.
- **Компилятор:** GCC (или Clang)
- **Библиотеки:** OpenSSL

Установка зависимостей (Ubuntu/Debian):

```bash
sudo apt install build-essential libssl-dev
```

### Клиент

- **ОС:** любая (Linux, Windows, macOS)
- **Python:** 3.8 или новее
- **Зависимости:** на Linux может потребоваться `tkinter`

```bash
sudo apt install python3-tk
```

## Быстрый старт (Docker)

Требуется установленный Docker (на Windows — Docker Desktop с WSL 2).

**1. Сгенерировать сертификаты:**

```bash
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
```

**2. Собрать образ:**

```bash
docker build -t terminal-chat-server .
```

**3. Запустить контейнер:**

```bash
docker run -d --name chat-server -p 5050:5050 \
  -v $(pwd)/server.key:/app/server.key:ro \
  -v $(pwd)/server.crt:/app/server.crt:ro \
  terminal-chat-server
```

**4. Запустить клиент:**

```bash
python3 chat_app.py
```

В окне клиента:

- **host:** `127.0.0.1`
- **port:** `5050`
- **name:** любое

## Запуск без Docker

### Сборка сервера

```bash
gcc server.c -o server -lssl -lcrypto
```

### Генерация SSL-сертификатов

Сертификаты **не хранятся в репозитории** — сгенерируйте свои:

```bash
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
```

После этого появятся `server.key` и `server.crt` (уже в `.gitignore`).

### Запуск

**Сервер:**

```bash
./server
```

Сервер слушает порт **5050**.

**Клиент:**

```bash
python3 chat_app.py
```

## Команды в чате

- `/quit` или `/exit` — выйти
- `/clear` — очистить экран

## Подключение с разных устройств

**В одной локальной сети:**

- Если сервер на этом же ПК — IP `127.0.0.1`
- Если сервер на другом устройстве — IP этого устройства (узнать командой `ip a`)
- Порт `5050`

**Не в одной локальной сети:**

Использовать утилиты вроде RadminVPN, ZeroTier и т.д. для создания локальной сети.

- IP — адрес хоста, присвоенный ему в новой сети
- Порт `5050`

## Полезные команды Docker

```bash
docker ps                    # запущенные контейнеры
docker ps -a                 # все, включая остановленные
docker logs chat-server      # логи
docker logs -f chat-server   # логи в реальном времени
docker stop chat-server      # остановить
docker start chat-server     # запустить снова
docker rm -f chat-server     # удалить
```

## Планы

- [ ] Групповые чаты
- [ ] Отправка файлов
- [ ] Поддержка множества комнат
