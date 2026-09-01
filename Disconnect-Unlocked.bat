@echo off
powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c for /f ""tokens=3"" %%s in (''query user %USERNAME%'') do tscon %%s /dest:console' -Verb RunAs"
