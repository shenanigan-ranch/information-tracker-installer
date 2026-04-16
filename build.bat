@echo off
setlocal EnableExtensions EnableDelayedExpansion
echo Building ShenaniganRanchInformationTrackerInstaller.exe...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "ShenaniganRanchInformationTrackerInstaller" installer.py
if %ERRORLEVEL% EQU 0 (
    set "EXE_PATH=dist\ShenaniganRanchInformationTrackerInstaller.exe"
    echo.
    echo Signing !EXE_PATH! with self-signed development certificate...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { param([string]$FilePath) $ErrorActionPreference='Stop'; $subject='CN=ShenaniganRanch Dev Code Signing'; $cert=Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $subject -and $_.HasPrivateKey } | Sort-Object NotAfter -Descending | Select-Object -First 1; if (-not $cert) { $cert=New-SelfSignedCertificate -Type CodeSigningCert -Subject $subject -CertStoreLocation 'Cert:\CurrentUser\My' -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(3) }; $sig=Set-AuthenticodeSignature -FilePath $FilePath -Certificate $cert -HashAlgorithm SHA256; Write-Host ('Sign status: ' + $sig.Status); Write-Host ('Signer thumbprint: ' + $cert.Thumbprint) }" -FilePath "!EXE_PATH!"
    if errorlevel 1 (
        echo.
        echo Signing failed with error code !ERRORLEVEL!
        pause
        exit /b !ERRORLEVEL!
    )
    echo.
    echo Build successful!
    echo EXE location: !EXE_PATH!
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
)
pause
