"""
view/ai_window.py
-----------------
Modern AI Assistant Chat Window — floating Toplevel for the Clinic app.

Design: dark navy glassmorphism, gradient accents, smooth animations,
matching the sidebar palette (#1E2A3A / #2563EB).
"""

import customtkinter as ctk
import tkinter as tk
import sys, os, threading
from datetime import datetime

# Ensure ai-core is importable
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AI_CORE = os.path.join(_PROJECT, "ai-core")
if _AI_CORE not in sys.path:
    sys.path.insert(0, _AI_CORE)

from ai_worker import AIWorker


# ── Palette ───────────────────────────────────────────────────────────
_P = {
    "win_bg":        "#0F172A",
    "header_bg":     "#1E2A3A",
    "input_bg":      "#1E2A3A",
    "chat_bg":       "#0F172A",
    "user_bubble":   "#2563EB",
    "ai_bubble":     "#1E293B",
    "ai_bubble_bdr": "#334155",
    "accent":        "#3B82F6",
    "accent_hover":  "#2563EB",
    "text_primary":  "#F1F5F9",
    "text_secondary":"#94A3B8",
    "text_dim":      "#64748B",
    "danger":        "#EF4444",
    "danger_hover":  "#DC2626",
    "divider":       "#1E293B",
    "scrollbar":     "#334155",
    "typing_dot":    "#3B82F6",
}

FONT = "Segoe UI"


class AIAssistantWindow(ctk.CTkToplevel):
    """Floating AI chat window — one instance managed by ClinicApp."""

    WIDTH  = 420
    HEIGHT = 620

    def __init__(self, parent, llm_service):
        super().__init__(parent)

        self.llm_service = llm_service
        self._is_waiting = False
        self._typing_dots = 0
        self._typing_after_id = None

        # ── Window chrome ─────────────────────────────────────────────
        self.title("AI Assistant")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(360, 480)
        self.configure(fg_color=_P["win_bg"])
        self.resizable(True, True)
        self.transient(parent)
        self.lift()
        self.focus_force()

        # Try to set window icon (non-critical)
        try:
            self.after(200, lambda: self.iconbitmap(""))
        except Exception:
            pass

        # ── Layout grid ───────────────────────────────────────────────
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # chat area expands

        self._build_header()
        self._build_chat_area()
        self._build_input_bar()

        # Welcome message
        self._append_ai_message(
            "Bonjour ! 👋 Je suis votre assistant médical IA.\n\n"
            "Je peux vous aider avec :\n"
            "• Résumés de dossiers patients\n"
            "• Suggestions diagnostiques\n"
            "• Gestion des rendez-vous\n"
            "• Questions médicales générales\n\n"
            "Comment puis-je vous aider ?"
        )

    # ═══════════════════════ HEADER ═══════════════════════════════════

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=_P["header_bg"],
                              corner_radius=0, height=62)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        # AI avatar
        avatar = ctk.CTkFrame(header, fg_color=_P["accent"],
                              width=36, height=36, corner_radius=18)
        avatar.grid(row=0, column=0, padx=(16, 10), pady=13)
        avatar.grid_propagate(False)
        ctk.CTkLabel(avatar, text="🤖", font=ctk.CTkFont(size=16)
                     ).place(relx=0.5, rely=0.5, anchor="center")

        # Title + subtitle
        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.grid(row=0, column=1, sticky="w", pady=10)

        ctk.CTkLabel(titles, text="Assistant IA",
                     font=ctk.CTkFont(FONT, 15, "bold"),
                     text_color=_P["text_primary"]
                     ).pack(anchor="w")

        self._status_label = ctk.CTkLabel(
            titles, text="● En ligne",
            font=ctk.CTkFont(FONT, 11),
            text_color="#22C55E"
        )
        self._status_label.pack(anchor="w")

        # Clear chat button
        ctk.CTkButton(
            header, text="🗑", width=34, height=34,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=_P["divider"],
            text_color=_P["text_dim"],
            corner_radius=8,
            command=self._clear_chat
        ).grid(row=0, column=2, padx=(4, 12), pady=14)

    # ═══════════════════════ CHAT AREA ════════════════════════════════

    def _build_chat_area(self):
        # Outer container
        chat_container = ctk.CTkFrame(self, fg_color=_P["chat_bg"],
                                       corner_radius=0)
        chat_container.grid(row=1, column=0, sticky="nsew")
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(0, weight=1)

        # Scrollable frame for messages
        self._chat_scroll = ctk.CTkScrollableFrame(
            chat_container,
            fg_color=_P["chat_bg"],
            scrollbar_button_color=_P["scrollbar"],
            scrollbar_button_hover_color=_P["accent"],
            corner_radius=0,
        )
        self._chat_scroll.grid(row=0, column=0, sticky="nsew")
        self._chat_scroll.grid_columnconfigure(0, weight=1)

        self._message_row = 0

    # ═══════════════════════ INPUT BAR ════════════════════════════════

    def _build_input_bar(self):
        # Divider
        ctk.CTkFrame(self, fg_color=_P["divider"],
                     height=1).grid(row=2, column=0, sticky="ew")

        bar = ctk.CTkFrame(self, fg_color=_P["input_bg"],
                           corner_radius=0, height=64)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)

        # Text input
        self._input = ctk.CTkTextbox(
            bar, height=38,
            fg_color="#0F172A",
            border_width=1,
            border_color=_P["divider"],
            text_color=_P["text_primary"],
            font=ctk.CTkFont(FONT, 13),
            corner_radius=12,
            wrap="word",
        )
        self._input.grid(row=0, column=0, padx=(12, 8), pady=13, sticky="ew")
        self._input.bind("<Return>", self._on_enter)
        self._input.bind("<Shift-Return>", self._on_shift_enter)

        # Focus the input
        self.after(300, lambda: self._input.focus_set())

        # Send button
        self._send_btn = ctk.CTkButton(
            bar, text="➤", width=40, height=38,
            font=ctk.CTkFont(size=18),
            fg_color=_P["accent"],
            hover_color=_P["accent_hover"],
            text_color="#FFFFFF",
            corner_radius=12,
            command=self._on_send
        )
        self._send_btn.grid(row=0, column=1, padx=(0, 12), pady=13)

    # ═══════════════════════ MESSAGE BUBBLES ══════════════════════════

    def _append_user_message(self, text: str):
        """Add a right-aligned user bubble."""
        row = self._message_row
        self._message_row += 1

        wrapper = ctk.CTkFrame(self._chat_scroll, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="e", padx=(50, 8), pady=(4, 2))

        bubble = ctk.CTkFrame(wrapper, fg_color=_P["user_bubble"],
                              corner_radius=16)
        bubble.pack(anchor="e")

        ctk.CTkLabel(
            bubble, text=text,
            font=ctk.CTkFont(FONT, 13),
            text_color="#FFFFFF",
            wraplength=280,
            justify="left",
            anchor="w",
        ).pack(padx=14, pady=(10, 4))

        # Timestamp
        ts = datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            bubble, text=ts,
            font=ctk.CTkFont(FONT, 9),
            text_color="#93A3D1",
            anchor="e",
        ).pack(padx=14, pady=(0, 8), anchor="e")

        self._scroll_to_bottom()

    def _append_ai_message(self, text: str):
        """Add a left-aligned AI bubble."""
        row = self._message_row
        self._message_row += 1

        wrapper = ctk.CTkFrame(self._chat_scroll, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="w", padx=(8, 50), pady=(4, 2))

        # Small avatar
        top_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        top_row.pack(anchor="w", pady=(0, 2))

        mini_av = ctk.CTkFrame(top_row, fg_color=_P["accent"],
                               width=22, height=22, corner_radius=11)
        mini_av.pack(side="left", padx=(0, 6))
        mini_av.pack_propagate(False)
        ctk.CTkLabel(mini_av, text="🤖", font=ctk.CTkFont(size=10)
                     ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(top_row, text="Assistant IA",
                     font=ctk.CTkFont(FONT, 10, "bold"),
                     text_color=_P["text_secondary"]
                     ).pack(side="left")

        bubble = ctk.CTkFrame(wrapper, fg_color=_P["ai_bubble"],
                              border_width=1,
                              border_color=_P["ai_bubble_bdr"],
                              corner_radius=16)
        bubble.pack(anchor="w")

        ctk.CTkLabel(
            bubble, text=text,
            font=ctk.CTkFont(FONT, 13),
            text_color=_P["text_primary"],
            wraplength=280,
            justify="left",
            anchor="w",
        ).pack(padx=14, pady=(10, 4))

        ts = datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            bubble, text=ts,
            font=ctk.CTkFont(FONT, 9),
            text_color=_P["text_dim"],
            anchor="e",
        ).pack(padx=14, pady=(0, 8), anchor="e")

        self._scroll_to_bottom()

    # ═══════════════════════ TYPING INDICATOR ═════════════════════════

    def _show_typing(self):
        """Show animated 'typing...' indicator."""
        row = self._message_row  # don't increment — will be replaced
        self._typing_row = row

        self._typing_wrapper = ctk.CTkFrame(
            self._chat_scroll, fg_color="transparent")
        self._typing_wrapper.grid(
            row=row, column=0, sticky="w", padx=(8, 50), pady=(4, 2))

        bubble = ctk.CTkFrame(self._typing_wrapper,
                              fg_color=_P["ai_bubble"],
                              border_width=1,
                              border_color=_P["ai_bubble_bdr"],
                              corner_radius=16)
        bubble.pack(anchor="w")

        self._typing_label = ctk.CTkLabel(
            bubble, text="●  ●  ●",
            font=ctk.CTkFont(FONT, 14, "bold"),
            text_color=_P["typing_dot"],
        )
        self._typing_label.pack(padx=18, pady=12)

        self._typing_dots = 0
        self._animate_typing()
        self._scroll_to_bottom()

    def _animate_typing(self):
        """Cycle through dot animation frames."""
        if not self._is_waiting:
            return
        frames = [
            "●  ○  ○",
            "○  ●  ○",
            "○  ○  ●",
            "●  ●  ○",
            "○  ●  ●",
            "●  ●  ●",
        ]
        self._typing_dots = (self._typing_dots + 1) % len(frames)
        try:
            self._typing_label.configure(text=frames[self._typing_dots])
        except Exception:
            return
        self._typing_after_id = self.after(350, self._animate_typing)

    def _hide_typing(self):
        """Remove typing indicator."""
        if self._typing_after_id:
            self.after_cancel(self._typing_after_id)
            self._typing_after_id = None
        try:
            self._typing_wrapper.destroy()
        except Exception:
            pass

    # ═══════════════════════ SEND LOGIC ═══════════════════════════════

    def _on_enter(self, event):
        """Send on Enter (without Shift)."""
        self._on_send()
        return "break"  # prevent newline insertion

    def _on_shift_enter(self, event):
        """Allow newline on Shift+Enter."""
        return  # default behavior — insert newline

    def _on_send(self):
        if self._is_waiting:
            return

        raw = self._input.get("1.0", "end").strip()
        if not raw:
            return

        self._input.delete("1.0", "end")
        self._append_user_message(raw)

        # Disable input while waiting
        self._is_waiting = True
        self._send_btn.configure(state="disabled",
                                 fg_color=_P["text_dim"])
        self._status_label.configure(text="● Réflexion...",
                                     text_color="#F59E0B")
        self._show_typing()

        # Run in background thread — use "agent" mode so the model
        # can invoke database tools (get_patient_record, get_today_appointments…)
        worker = AIWorker(
            service=self.llm_service,
            mode="agent",
            payload={"message": raw},
            callback=lambda result: self.after(0, self._on_response, result),
            error_callback=lambda err: self.after(0, self._on_error, err),
        )
        worker.start()

    def _on_response(self, result: str):
        """Handle AI response (called on main thread via .after)."""
        self._hide_typing()
        self._append_ai_message(result)
        self._reset_input_state()

    def _on_error(self, error: str):
        """Handle error (called on main thread via .after)."""
        self._hide_typing()
        self._append_ai_message(f"⚠️ Erreur : {error}")
        self._reset_input_state()

    def _reset_input_state(self):
        self._is_waiting = False
        self._send_btn.configure(state="normal",
                                 fg_color=_P["accent"])
        self._status_label.configure(text="● En ligne",
                                     text_color="#22C55E")
        self._input.focus_set()

    # ═══════════════════════ UTILITIES ════════════════════════════════

    def _clear_chat(self):
        """Remove all messages and reset LLM history."""
        for widget in self._chat_scroll.winfo_children():
            widget.destroy()
        self._message_row = 0
        self.llm_service.reset_history()

        self._append_ai_message(
            "Conversation effacée. 🧹\nComment puis-je vous aider ?"
        )

    def _scroll_to_bottom(self):
        """Scroll chat to the latest message."""
        self.after(80, lambda: self._chat_scroll._parent_canvas.yview_moveto(1.0))
