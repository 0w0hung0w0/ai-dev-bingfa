@echo off
rem dev-bingfa-check: PostToolUse entry for Codex on Windows (Codex runs commandWindows with cmd.exe /C).
rem Claude Code never runs this file. It is the same as "run.cmd post": post_check.py reads both
rem Claude Code and Codex (apply_patch) payloads, so every tool and OS ends in the same checker.
call "%~dp0run.cmd" post
exit /b %ERRORLEVEL%
