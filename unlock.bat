@echo off
for /f "skip=1 tokens=3" %%s in ('query user %USERNAME%') do (
    %windir%\System32\tscon.exe %%s /dest:console
)
for /f "tokens=2" %%i in ('qwinsta ^| findstr /i "Active"') do (
    %windir%\System32\tscon.exe %%i /dest:console
)
