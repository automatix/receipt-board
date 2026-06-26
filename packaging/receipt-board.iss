; Receipt Board - Inno Setup installer.
;
; Per-machine install of the PyInstaller `onedir` build (dist\receipt-board\) into
; {autopf}\Receipt Board, with a Start-menu shortcut and an automatic uninstaller
; (Apps & features registration).
;
; This is the build-foundation script (issue #58): it compiles and produces a working
; setup.exe. The optional desktop shortcut and the keep-vs-remove user-data prompt on
; uninstall are added in issue #60.
;
; Stable application identity - CONSTANT across versions (do not change):
;   reverse-DNS id : com.automatix.receipt-board
;   AppId GUID     : {6E5EAF6B-4A26-4DCC-AD31-D72D47D602E4}
;
; The version is supplied by scripts\build-installer.ps1 via /DAppVersion=<x.y.z>.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

#define AppName "Receipt Board"
#define AppPublisher "Ilya Khanataev"
#define AppExeName "receipt-board.exe"

[Setup]
; The leading double-brace escapes to a literal "{" so AppId = {6E5EAF6B-...}.
AppId={{6E5EAF6B-4A26-4DCC-AD31-D72D47D602E4}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
; Resolve all relative paths from the repo root (this script lives in packaging\).
SourceDir={#SourcePath}..
OutputDir=dist\installer
OutputBaseFilename=receipt-board-v{#AppVersion}-setup
DefaultDirName={autopf}\Receipt Board
DefaultGroupName=Receipt Board
DisableProgramGroupPage=yes
; Per-machine install into Program Files -> requires elevation (UAC).
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=packaging\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes

[Files]
; Install the entire onedir tree (receipt-board.exe + _internal\).
Source: "dist\receipt-board\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Receipt Board"; Filename: "{app}\{#AppExeName}"
