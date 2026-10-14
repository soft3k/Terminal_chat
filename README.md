## Terminal chat

Простой терминальный чат: Сервер на С, клиент на Python.

# Стек технологий

- **Сервер** С
- **Клиент** Python 3
- **Транспорт** TCP/IP с SSL/TLS шифрованием

# Структура проекта

```
terminal_chat/
├── chat_app.py # Python-клиент
├── server.c # Исходник сервера на C
├── server.crt.example # Пример: как сгенерировать SSL-сертификаты
└── .gitignore
```

# Сборка сервера

```bash
gcc server.c -o server -lssl -lcrypto
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
```

# Запуск сервера

```bash
./server
```

*Сервер слушает порт 5050*

# Запуск клиента

```bash
python3 chat_app.py
```

# Требования

# Сервер

- *OS* Linux(Ubuntu,Debian,Arch и др.)
Сервер использует стандартные библиотеки С, POSIX-сокеты и OpenSSL
и **не собирается** на нативном Windows 
- *Компилятор* GCC (или Clang)
- *Библиотеки* OpenSSL

*Установка зависимостей (Ubuntu/Debian):*

```bash
sudo apt install build-essential libssl-dev
```

# Клиент

- **ОС** Любая(Linux,Windows,macOS)
- **Python:** v3.8 или новее
- **Зависимости** На Linux может потребоваться установка `tkinter`

```bash
sudo apt install python3-tk
```

# Как подключиться к серверу с разных устройств

**Находясь в одной локальной сети**

- Если подключение с одного устройства — IP `127.0.0.1`
- Если с разных устройств — IP устройства, на котором запущен сервер
- Порт `5050`

**Не находясь в одной локальной сети**

Использовать утилиты вроде RadminVPN, ZeroTier и т.д.
для создания локальной сети.

- IP — адрес хоста, присвоенный ему в новой сети
- Порт `5050`
