@REM ----------------------------------------------------------------------------
@REM Maven Wrapper startup script
@REM ----------------------------------------------------------------------------

@if "%DEBUG%"=="" @echo off
@REM Find the project base directory
set "MAVEN_PROJECTBASEDIR=%~dp0"
set "WRAPPER_JAR=%MAVEN_PROJECTBASEDIR%.mvn\wrapper\maven-wrapper.jar"

if not exist "%WRAPPER_JAR%" (
    echo Maven Wrapper JAR not found: %WRAPPER_JAR%
    exit /b 1
)

set "JAVA_EXE=java.exe"
"%JAVA_EXE%" -jar "%WRAPPER_JAR%" %*
