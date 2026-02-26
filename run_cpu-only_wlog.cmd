@echo off
setlocal

set "SCRIPTROOT=%~dp0"
set "PYTHON_BIN=%SCRIPTROOT%python\python.exe"
set "OLLAMA_BIN=%SCRIPTROOT%ollama\ollama.exe"

@REM NVIDIA disable
set "CUDA_VISIBLE_DEVICES=-1"
@REM AMD disable
set "ROCR_VISIBLE_DEVICES=-1"
@REM Intel disable
set "GGML_VK_VISIBLE_DEVICES=-1"

@REM Avoid port conflict
set "OLLAMA_HOST=http://127.0.0.1:11435"

set "OLLAMA_MODELS=%SCRIPTROOT%models"

echo Starting Ollama (CPU-Only + wLog)...
start /B "" "%OLLAMA_BIN%" serve
timeout /t 3 /nobreak >nul

echo Starting Local AI OCR...
"%PYTHON_BIN%" "%SCRIPTROOT%src\main.py"

echo Stopping Ollama...
taskkill /F /IM ollama.exe

endlocal
echo.
pause