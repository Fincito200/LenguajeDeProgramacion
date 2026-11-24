@echo off
setlocal
title Monopoly - Java original

rem Abre el proyecto Java original sin modificar sus fuentes ni sus recursos.
set "PROYECTO=%~dp0..\ProyectoFinalPOO"
if not exist "%PROYECTO%\src\proyectofinalpoo\Principal.java" (
    echo No se encontro ProyectoFinalPOO junto a LenguajeDeProgramacion.
    pause
    exit /b 1
)

rem Usa Java del mismo JDK que javac para evitar mezclar versiones instaladas.
set "JAVAC="
for /f "delims=" %%J in ('where javac.exe 2^>nul') do if not defined JAVAC set "JAVAC=%%J"
if not defined JAVAC if defined JAVA_HOME if exist "%JAVA_HOME%\bin\javac.exe" set "JAVAC=%JAVA_HOME%\bin\javac.exe"
if not defined JAVAC (
    echo Hace falta un JDK con javac disponible en PATH o JAVA_HOME.
    pause
    exit /b 1
)
for %%J in ("%JAVAC%") do set "JAVA=%%~dpJjava.exe"
if not exist "%JAVA%" (
    echo No se encontro java.exe junto a javac.exe.
    pause
    exit /b 1
)

pushd "%PROYECTO%" || exit /b 1
echo Compilando la version Java original...
"%JAVAC%" -encoding UTF-8 -cp "lib\AbsoluteLayout-RELEASE300.jar" -d "build\launcher-java" src\proyectofinalpoo\*.java
if errorlevel 1 (
    echo No se pudo compilar el proyecto Java.
    popd
    pause
    exit /b 1
)

echo Abriendo Monopoly en Java...
"%JAVA%" -cp "build\launcher-java;src;lib\AbsoluteLayout-RELEASE300.jar" proyectofinalpoo.Principal
set "RESULTADO=%ERRORLEVEL%"
popd
if not "%RESULTADO%"=="0" pause
exit /b %RESULTADO%
