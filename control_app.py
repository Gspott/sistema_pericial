#!/usr/bin/env python3

from __future__ import annotations

import logging
import os
import queue
import socket
import subprocess
import threading
from pathlib import Path
import tkinter as tk


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = Path(PROJECT_ROOT)
STATUS_SCRIPT = PROJECT_DIR / "status.sh"
START_SCRIPT = PROJECT_DIR / "start_all.sh"
STOP_SCRIPT = PROJECT_DIR / "stop_all.sh"
ICON_PATH = PROJECT_DIR / "icono_servidor_tahoe.png"
LOG_PATH = PROJECT_DIR / "logs" / "control_app.log"
REFRESH_MS = 3000
MACOS_GUI_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

RUNNING_COLOR = "#2ecc71"
STOPPED_COLOR = "#e74c3c"
RUNNING_ACTIVE_COLOR = "#27ae60"
STOPPED_ACTIVE_COLOR = "#c0392b"
WINDOW_BG = "#f7f4ee"
TEXT_COLOR = "#ffffff"
DIAG_OK_COLOR = RUNNING_ACTIVE_COLOR
DIAG_OFF_COLOR = "#8c8c8c"

class MacStatusItem:
    def __init__(self, on_activate) -> None:
        self.on_activate = on_activate

    def update(self, state: str) -> None:
        return


class ControlApp:
    def __init__(self) -> None:
        self._setup_logging()
        logging.info("Detected project root: %s", PROJECT_ROOT)
        self.root = tk.Tk()
        self.root.title("Control Servidor")
        self.root.geometry("380x360")
        self.root.resizable(False, False)
        self.root.configure(bg=WINDOW_BG)
        self.app_icon = None

        self.state = "STOPPED"
        self.action_in_progress = False
        self.refresh_in_progress = False
        self.action_label = None
        self.hovered = False
        self.canvas_width = 300
        self.canvas_height = 128
        self.ui_queue: queue.SimpleQueue[tuple[str, object]] = queue.SimpleQueue()
        self.diagnostic_labels: dict[str, tk.Label] = {}

        container = tk.Frame(self.root, bg=WINDOW_BG, padx=28, pady=28)
        container.pack(fill="both", expand=True)

        self.button = tk.Canvas(
            container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=WINDOW_BG,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.button.pack(expand=True, fill="x", pady=(18, 12))
        self.button.bind("<Button-1>", self._on_button_click)
        self.button.bind("<Enter>", self._on_hover_enter)
        self.button.bind("<Leave>", self._on_hover_leave)

        self.button_rect = self.button.create_rectangle(
            4,
            4,
            self.canvas_width - 4,
            self.canvas_height - 4,
            width=2,
            outline=STOPPED_ACTIVE_COLOR,
            fill=STOPPED_COLOR,
        )
        self.button_text = self.button.create_text(
            self.canvas_width // 2,
            self.canvas_height // 2,
            text="INICIAR SERVIDOR",
            fill=TEXT_COLOR,
            font=("Helvetica", 20, "bold"),
            justify="center",
        )

        self.status_label = tk.Label(
            container,
            text="Estado: apagado",
            font=("Helvetica", 14, "bold"),
            bg=WINDOW_BG,
        )
        self.status_label.pack(pady=(0, 10))

        diagnostics_frame = tk.Frame(container, bg=WINDOW_BG)
        diagnostics_frame.pack(fill="x", pady=(4, 0))

        for key, title in (
            ("fastapi", "FastAPI"),
            ("caddy", "Caddy"),
            ("caffeinate", "caffeinate"),
            ("duckdns", "DuckDNS"),
        ):
            row = tk.Frame(diagnostics_frame, bg=WINDOW_BG)
            row.pack(fill="x", anchor="w")
            tk.Label(
                row,
                text=f"{title}:",
                font=("Helvetica", 10),
                fg="#4a4a4a",
                bg=WINDOW_BG,
                anchor="w",
            ).pack(side="left")
            value_label = tk.Label(
                row,
                text="OFF",
                font=("Helvetica", 10, "bold"),
                fg=DIAG_OFF_COLOR,
                bg=WINDOW_BG,
                anchor="w",
            )
            value_label.pack(side="left", padx=(6, 0))
            self.diagnostic_labels[key] = value_label

        self._configure_app_icon()
        self.status_item = MacStatusItem(self._show_window)
        self._apply_state("STOPPED")
        self._apply_diagnostics(self._get_component_diagnostics())
        self.root.after(100, self._process_ui_queue)
        self.refresh_state()

    def run(self) -> None:
        self.root.mainloop()

    def refresh_state(self) -> None:
        if self.refresh_in_progress:
            return

        self.refresh_in_progress = True
        threading.Thread(target=self._refresh_state_worker, daemon=True).start()

    def _refresh_state_worker(self) -> None:
        try:
            state = self._get_state()
            diagnostics = self._get_component_diagnostics()
            self.ui_queue.put(("refresh", {"state": state, "diagnostics": diagnostics}))
        except Exception:
            logging.exception("Error refreshing server state")
            self.ui_queue.put(
                ("refresh", {"state": "STOPPED", "diagnostics": self._get_component_diagnostics()})
            )

    def _get_state(self) -> str:
        try:
            result = subprocess.run(
                ["/bin/bash", str(STATUS_SCRIPT)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
                env=self._build_script_env(),
            )
            logging.info(
                "Status command: %s | cwd=%s | PATH=%s | stdout=%s | stderr=%s",
                ["/bin/bash", str(STATUS_SCRIPT)],
                PROJECT_ROOT,
                self._build_script_env().get("PATH", ""),
                result.stdout.strip(),
                result.stderr.strip(),
            )
            if "RUNNING" in result.stdout:
                return "RUNNING"
        except Exception:
            logging.exception("Error running status script")
        return "STOPPED"

    def _apply_state(self, state: str) -> None:
        self.state = state

        if state == "RUNNING":
            button_text = "DETENER SERVIDOR"
            button_bg = RUNNING_COLOR
            button_active_bg = RUNNING_ACTIVE_COLOR
            status_text = "Estado: activo"
            status_color = RUNNING_ACTIVE_COLOR
        else:
            button_text = "INICIAR SERVIDOR"
            button_bg = STOPPED_COLOR
            button_active_bg = STOPPED_ACTIVE_COLOR
            status_text = "Estado: apagado"
            status_color = STOPPED_ACTIVE_COLOR

        if self.action_in_progress and self.action_label:
            button_text = self.action_label

        fill_color = button_active_bg if self.hovered and not self.action_in_progress else button_bg
        outline_color = button_active_bg
        text_color = "#f3f3f3" if self.action_in_progress else TEXT_COLOR
        cursor = "arrow" if self.action_in_progress else "hand2"

        self.button.itemconfigure(
            self.button_rect,
            fill=fill_color,
            outline=outline_color,
        )
        self.button.itemconfigure(
            self.button_text,
            text=button_text,
            fill=text_color,
        )
        self.button.configure(cursor=cursor)
        self.status_label.configure(text=status_text, fg=status_color)
        self.status_item.update(state)

    def _finish_refresh(self, state: str) -> None:
        self.refresh_in_progress = False
        self._apply_state(state)
        self.root.after(REFRESH_MS, self.refresh_state)

    def _apply_diagnostics(self, diagnostics: dict[str, tuple[str, str]]) -> None:
        for key, label in self.diagnostic_labels.items():
            value_text, color = diagnostics.get(key, ("OFF", DIAG_OFF_COLOR))
            label.configure(text=value_text, fg=color)

    def toggle_server(self) -> None:
        if self.action_in_progress:
            return

        self.action_in_progress = True
        if self.state == "STOPPED":
            self.action_label = "INICIANDO..."
            target_script = START_SCRIPT
        else:
            self.action_label = "DETENIENDO..."
            target_script = STOP_SCRIPT

        self._apply_state(self.state)
        threading.Thread(
            target=self._run_script_worker,
            args=(target_script,),
            daemon=True,
        ).start()

    def _run_script_worker(self, script_path: Path) -> None:
        command = ["/bin/bash", str(script_path)]
        env = self._build_script_env()
        try:
            logging.info(
                "Executing command: %s | cwd=%s | PATH=%s",
                command,
                PROJECT_ROOT,
                env.get("PATH", ""),
            )
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            stdout, stderr = process.communicate()
            logging.info("Command exit code for %s: %s", script_path, process.returncode)
            if stdout:
                logging.info("stdout %s:\n%s", script_path.name, stdout.strip())
            if stderr:
                logging.info("stderr %s:\n%s", script_path.name, stderr.strip())
        except Exception:
            logging.exception("Error running action script: %s", script_path)
        self.ui_queue.put(("action_complete", None))

    def _complete_action(self) -> None:
        self.action_in_progress = False
        self.action_label = None
        self.refresh_state()

    def _on_button_click(self, _event: tk.Event) -> None:
        if self.action_in_progress:
            return
        self.toggle_server()

    def _on_hover_enter(self, _event: tk.Event) -> None:
        self.hovered = True
        self._apply_state(self.state)

    def _on_hover_leave(self, _event: tk.Event) -> None:
        self.hovered = False
        self._apply_state(self.state)

    def _configure_app_icon(self) -> None:
        if not ICON_PATH.exists():
            return

        try:
            self.app_icon = tk.PhotoImage(file=str(ICON_PATH))
            self.root.iconphoto(True, self.app_icon)
        except Exception:
            self.app_icon = None

    def _show_window(self) -> None:
        self.root.after(0, self._show_window_on_main_thread)

    def _show_window_on_main_thread(self) -> None:
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            logging.exception("Error showing main window")

    def _process_ui_queue(self) -> None:
        try:
            while True:
                action, value = self.ui_queue.get_nowait()
                if action == "refresh":
                    payload = value if isinstance(value, dict) else {}
                    self._apply_diagnostics(payload.get("diagnostics", {}))
                    self._finish_refresh(str(payload.get("state", "STOPPED")))
                elif action == "action_complete":
                    self._complete_action()
        except queue.Empty:
            pass
        self.root.after(100, self._process_ui_queue)

    def _get_component_diagnostics(self) -> dict[str, tuple[str, str]]:
        duckdns_configured = bool(os.getenv("DUCKDNS_DOMAIN")) and bool(os.getenv("DUCKDNS_TOKEN"))
        return {
            "fastapi": self._status_display(self._is_port_open(8000), "OK", "OFF"),
            "caddy": self._status_display(self._is_process_active("caddy"), "OK", "OFF"),
            "caffeinate": self._status_display(self._is_process_active("caffeinate"), "OK", "OFF"),
            "duckdns": self._status_display(duckdns_configured, "configurado", "sin configurar"),
        }

    @staticmethod
    def _status_display(is_ok: bool, ok_text: str, off_text: str) -> tuple[str, str]:
        return (ok_text, DIAG_OK_COLOR) if is_ok else (off_text, DIAG_OFF_COLOR)

    @staticmethod
    def _is_process_active(process_name: str) -> bool:
        try:
            result = subprocess.run(
                ["pgrep", "-x", process_name],
                capture_output=True,
                text=True,
                check=False,
                env=ControlApp._build_script_env(),
            )
            return result.returncode == 0
        except Exception:
            logging.exception("Error checking process: %s", process_name)
            return False

    @staticmethod
    def _is_port_open(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            return False

    @staticmethod
    def _setup_logging() -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if logging.getLogger().handlers:
            return
        logging.basicConfig(
            filename=LOG_PATH,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )

    @staticmethod
    def _build_script_env() -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = MACOS_GUI_PATH
        env["HOME"] = os.path.expanduser("~")
        return env


if __name__ == "__main__":
    try:
        ControlApp().run()
    except Exception:
        ControlApp._setup_logging()
        logging.exception("Fatal error starting control_app")
        raise
