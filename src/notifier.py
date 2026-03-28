"""
notifier.py — Cross-platform notifications.
Uses plyer for desktop popups, falls back to terminal bell + print.
"""

import os
import sys


class Notifier:
    def __init__(self):
        self._plyer_available = self._check_plyer()

    def _check_plyer(self) -> bool:
        try:
            import plyer  # noqa: F401
            return True
        except ImportError:
            return False

    def notify(self, title: str, message: str, output_path: str = None):
        """Send desktop notification and print terminal summary."""
        # Terminal bell
        print("\a", end="", flush=True)

        # Desktop notification via plyer
        if self._plyer_available:
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name="PR Doc Generator",
                    timeout=8,
                )
                print(f"\n  🔔 Desktop notification sent.")
                return
            except Exception as e:
                # Gracefully degrade — not all environments support it
                pass

        # Fallback: coloured terminal output
        self._terminal_notify(title, message, output_path)

    def _terminal_notify(self, title: str, message: str, output_path: str):
        """Pretty terminal alert box."""
        width = 52
        border = "═" * width
        print(f"\n  ╔{border}╗")
        print(f"  ║  {title:<{width - 2}}║")
        print(f"  ╠{border}╣")
        for line in message.splitlines():
            print(f"  ║  {line:<{width - 2}}║")
        if output_path:
            short = output_path if len(output_path) <= width - 2 else "..." + output_path[-(width - 5):]
            print(f"  ║  {short:<{width - 2}}║")
        print(f"  ╚{border}╝")
