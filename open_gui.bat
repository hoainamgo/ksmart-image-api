@echo off
REM open_gui.bat - Mo endpoint ksmart trong trinh duyet tu cmd (Windows)
REM Chay: double-click hoac go "open_gui.bat" trong Command Prompt

set BASE=https://api.ksmart.com.es
set KEY=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf

echo ============================================
echo  KSMART API - Public Endpoint
echo  GUI : %BASE%/
echo  API : %BASE%/prompt  (can API key)
echo  Key : %KEY%
echo ============================================

REM Mo trang GUI trong trinh duyet mac dinh
start "" "%BASE%/"

REM (Tuy chon) test nhanh endpoint bang curl neu co san
where curl >nul 2>nul
if %errorlevel%==0 (
  echo.
  echo Kiem tra /queue (can key)...
  curl -s -o nul -w "HTTP %{http_code}\n" "%BASE%/queue?api_key=%KEY%"
)
pause
