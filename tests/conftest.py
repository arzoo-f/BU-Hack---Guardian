"""Test-wide safety: tests never reach the real OpenAI or Telegram, even through the module-level app.
(.env holds real keys; these switches make the server choose its fakes.)"""
import os

os.environ.setdefault("GUARDIAN_FAKE_AI", "1")
os.environ.setdefault("GUARDIAN_FAKE_TELEGRAM", "1")
