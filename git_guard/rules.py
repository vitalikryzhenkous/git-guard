"""Общие правила путей (используются аудитом и, позже, хуками)."""
import os

DENY_NAMES = {"pipeline.yaml", "profile.yaml", "facts.yaml", "log.jsonl"}
DENY_DIRS = {"reports"}


def denied_path(path):
    parts = path.split("/")
    base = parts[-1]
    return (base in DENY_NAMES or base.startswith(".env")
            or any(p in DENY_DIRS for p in parts[:-1]))


def is_test_path(path):
    parts = path.split("/")
    return any(p in ("tests", "test", "__tests__", "fixtures") for p in parts[:-1])
