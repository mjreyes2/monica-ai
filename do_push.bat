@echo off
setlocal
cd /d C:\Monica
for /f "tokens=*" %%i in ('gh auth token') do set GH_TOKEN=%%i
echo Token length: %GH_TOKEN:~0,4%...
git -c "credential.helper=" push https://mjreyes2:%GH_TOKEN%@github.com/mjreyes2/monica-ai.git master:main
echo PUSH_EXIT_CODE=%ERRORLEVEL%
endlocal
