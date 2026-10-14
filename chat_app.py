#!/usr/bin/env python3
"""
Secure Chat — клиент для TLS чат-сервера на C (порт 5050).
Только стандартная библиотека Python 3.8+: ничего не нужно компилировать.

Запуск:  python chat_app.py
"""
import queue
import socket
import ssl
import threading
import tkinter as tk
from tkinter import font as tkfont

# ── тема в стиле терминала ──────────────────────────────────────────────
BG = "#0d0f12"
PANEL = "#15181d"
BORDER = "#2a2f37"
FG = "#d7dae0"
DIM = "#6b7280"
GREEN = "#4ade80"
CYAN = "#67e8f9"
RED = "#f87171"
YELLOW = "#facc15"


class Connection:
    """TLS-соединение. Сеть живёт в отдельном потоке, события идут в очередь."""

    def __init__(self, events: queue.Queue):
        self.events = events
        self.sock = None
        self.alive = False
        self.lock = threading.Lock()

    def connect(self, host: str, port: int, name: str):
        threading.Thread(target=self._run, args=(host, port, name), daemon=True).start()

    def _run(self, host, port, name):
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            # сертификат самоподписанный — проверку отключаем
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            raw = socket.create_connection((host, port), timeout=8)
            self.sock = ctx.wrap_socket(raw, server_hostname=host)
            self.sock.settimeout(None)
            self.alive = True
            self.events.put(("connected", self.sock.version()))
            self.send(name)  # первое сообщение сервер принимает как имя
        except Exception as e:
            self.events.put(("error", f"{type(e).__name__}: {e}"))
            return

        buf = b""
        try:
            while self.alive:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data.replace(b"\x00", b"")
                *lines, buf = buf.split(b"\n")
                for line in lines:
                    self.events.put(("line", line.decode("utf-8", "replace").rstrip("\r")))
                # приглашение "Enter you name: " приходит без \n
                if buf.endswith(b": "):
                    self.events.put(("line", buf.decode("utf-8", "replace")))
                    buf = b""
        except OSError:
            pass
        if buf:
            self.events.put(("line", buf.decode("utf-8", "replace")))
        was_alive, self.alive = self.alive, False
        if was_alive:
            self.events.put(("closed", None))

    def send(self, text: str) -> bool:
        if not self.alive:
            return False
        try:
            with self.lock:
                self.sock.sendall((text + "\n").encode("utf-8"))
            return True
        except OSError as e:
            self.events.put(("error", str(e)))
            return False

    def close(self):
        self.alive = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.sock.close()
            self.sock = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("secure chat")
        self.geometry("720x480")
        self.minsize(480, 320)
        self.configure(bg=BG)

        family = next((f for f in ("JetBrains Mono", "Cascadia Mono", "Consolas", "Menlo",
                                   "DejaVu Sans Mono", "Courier New")
                       if f in tkfont.families()), "Courier")
        self.mono = (family, 12)
        self.mono_b = (family, 12, "bold")

        self.events = queue.Queue()
        self.conn = None
        self.name = ""

        self._build_connect()
        self._build_chat()
        self.show_connect()
        self.after(50, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._quit)

    # ── экраны ──────────────────────────────────────────────────────────
    def _entry(self, parent, value=""):
        e = tk.Entry(parent, font=self.mono, bg=PANEL, fg=FG, insertbackground=GREEN,
                     relief="flat", highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=GREEN)
        e.insert(0, value)
        return e

    def _build_connect(self):
        f = self.connect_frame = tk.Frame(self, bg=BG)
        box = tk.Frame(f, bg=BG)
        box.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(box, text="── secure chat ──", font=self.mono_b, bg=BG, fg=CYAN)\
            .grid(row=0, column=0, columnspan=2, pady=(0, 20))

        self.fields = {}
        for row, (key, label, default) in enumerate(
                [("host", "host", "127.0.0.1"), ("port", "port", "5050"), ("name", "name", "")], 1):
            tk.Label(box, text=f"{label} >", font=self.mono, bg=BG, fg=DIM, anchor="e", width=7)\
                .grid(row=row, column=0, padx=(0, 8), pady=4)
            e = self._entry(box, default)
            e.grid(row=row, column=1, ipady=5, pady=4, sticky="we")
            e.configure(width=26)
            e.bind("<Return>", lambda _e: self._do_connect())
            self.fields[key] = e

        self.connect_btn = tk.Button(box, text="[ connect ]", font=self.mono_b, bg=BG, fg=GREEN,
                                     activebackground=PANEL, activeforeground=GREEN, relief="flat",
                                     bd=0, cursor="hand2", command=self._do_connect)
        self.connect_btn.grid(row=4, column=1, sticky="w", pady=(14, 0))

        self.status = tk.Label(box, text="", font=self.mono, bg=BG, fg=DIM, wraplength=380,
                               justify="left")
        self.status.grid(row=5, column=0, columnspan=2, pady=(14, 0), sticky="w")

    def _build_chat(self):
        f = self.chat_frame = tk.Frame(self, bg=BG)

        top = tk.Frame(f, bg=PANEL)
        top.pack(side="top", fill="x")
        self.header = tk.Label(top, text="", font=self.mono, bg=PANEL, fg=DIM, anchor="w")
        self.header.pack(side="left", padx=12, pady=6)
        tk.Button(top, text="[ disconnect ]", font=self.mono, bg=PANEL, fg=RED, relief="flat",
                  bd=0, activebackground=PANEL, activeforeground=RED, cursor="hand2",
                  command=self._disconnect).pack(side="right", padx=12)

        # строка ввода пакуется ДО области сообщений: иначе Text забирает всё место
        bottom = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        bottom.pack(side="bottom", fill="x")
        tk.Label(bottom, text=">", font=self.mono_b, bg=PANEL, fg=GREEN).pack(side="left", padx=(12, 6))
        self.input = tk.Entry(bottom, font=self.mono, bg=PANEL, fg=FG, insertbackground=GREEN,
                              relief="flat", highlightthickness=0, disabledbackground=PANEL)
        self.input.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self.input.bind("<Return>", self._send)
        tk.Button(bottom, text="[ send ]", font=self.mono_b, bg=PANEL, fg=GREEN, relief="flat",
                  bd=0, activebackground=PANEL, activeforeground=GREEN, cursor="hand2",
                  command=self._send).pack(side="right", padx=(0, 12))

        body = tk.Frame(f, bg=BG)
        body.pack(fill="both", expand=True)
        self.log = tk.Text(body, font=self.mono, bg=BG, fg=FG, relief="flat", wrap="word",
                           height=1, padx=14, pady=10, state="disabled", cursor="arrow",
                           selectbackground=BORDER, highlightthickness=0)
        sb = tk.Scrollbar(body, command=self.log.yview, bg=BG, troughcolor=BG,
                          relief="flat", bd=0, width=10)
        self.log.configure(yscrollcommand=sb.set)
        self.log.bind("<Button-1>", lambda _e: self.input.focus_set())
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        for tag, color in (("dim", DIM), ("me", GREEN), ("nick", CYAN), ("err", RED),
                           ("sys", YELLOW), ("text", FG)):
            self.log.tag_configure(tag, foreground=color)

    def show_connect(self):
        self.chat_frame.pack_forget()
        self.connect_frame.pack(fill="both", expand=True)
        self.connect_btn.configure(state="normal", text="[ connect ]")
        (self.fields["name"] if self.fields["host"].get() else self.fields["host"]).focus_set()

    def show_chat(self):
        self.connect_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.after(50, self.input.focus_force)

    # ── действия ────────────────────────────────────────────────────────
    def _do_connect(self):
        if self.conn and self.conn.alive:
            return
        host = self.fields["host"].get().strip()
        port = self.fields["port"].get().strip() or "5050"
        name = self.fields["name"].get().strip()
        if not host:
            return self._status("укажи адрес сервера", RED)
        if not port.isdigit() or not 0 < int(port) < 65536:
            return self._status("порт — число от 1 до 65535", RED)
        if not name:
            return self._status("укажи имя", RED)
        self.name = name[:31]
        self.target = f"{host}:{port}"
        self._status(f"connecting to {self.target} ...", DIM)
        self.connect_btn.configure(state="disabled", text="[ ... ]")
        self.conn = Connection(self.events)
        self.conn.connect(host, int(port), self.name)

    def _send(self, _event=None):
        text = self.input.get().strip()
        if not text:
            return
        self.input.delete(0, "end")
        if text in ("/quit", "/exit"):
            return self._disconnect()
        if text == "/clear":
            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.configure(state="disabled")
            return
        if self.conn and self.conn.send(text):
            self._write(("you", "me"), (": ", "dim"), (text, "text"))

    def _disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        self._status("disconnected", DIM)
        self.show_connect()

    def _quit(self):
        if self.conn:
            self.conn.close()
        self.destroy()

    # ── вывод ───────────────────────────────────────────────────────────
    def _status(self, text, color):
        self.status.configure(text=text, fg=color)

    def _write(self, *parts):
        at_bottom = self.log.yview()[1] > 0.99
        self.log.configure(state="normal")
        for text, tag in parts:
            self.log.insert("end", text, tag)
        self.log.insert("end", "\n")
        self.log.configure(state="disabled")
        if at_bottom:
            self.log.see("end")

    def _show_line(self, line):
        if not line.strip():
            return
        if line.lower().startswith("enter you"):  # приглашение ввести имя — имя уже отправлено
            return
        if line.startswith("[") and "]: " in line:
            nick, msg = line[1:].split("]: ", 1)
            self._write((nick, "nick"), (": ", "dim"), (msg, "text"))
        else:
            self._write(("· " + line, "sys"))

    def _poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "connected":
                    self.header.configure(text=f"● {self.target}  ·  {self.name}  ·  {data}", fg=GREEN)
                    self.log.configure(state="normal")
                    self.log.delete("1.0", "end")
                    self.log.configure(state="disabled")
                    self._write((f"connected to {self.target} ({data})", "dim"))
                    self._write(("/quit — выйти, /clear — очистить экран", "dim"))
                    self.show_chat()
                elif kind == "line":
                    self._show_line(data)
                elif kind == "closed":
                    self._write(("✗ server closed the connection", "err"))
                    self.header.configure(text=f"○ {self.target}  ·  offline", fg=RED)
                elif kind == "error":
                    if self.chat_frame.winfo_ismapped():
                        self._write(("✗ " + data, "err"))
                    else:
                        self._status("✗ " + data, RED)
                        self.connect_btn.configure(state="normal", text="[ connect ]")
        except queue.Empty:
            pass
        self.after(50, self._poll)


if __name__ == "__main__":
    App().mainloop()
