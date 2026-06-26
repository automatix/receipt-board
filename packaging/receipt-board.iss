; Receipt Board - Inno Setup installer + uninstaller.
;
; Per-machine install of the PyInstaller `onedir` build (dist\receipt-board\) into
; {autopf}\Receipt Board, with a Start-menu shortcut, an optional desktop shortcut, and
; an automatic uninstaller (Apps & features registration). On uninstall it offers to
; remove the user's data (keep is the default; never during a silent/automated run).
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

[Tasks]
; Optional desktop shortcut (off by default).
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Install the entire onedir tree (receipt-board.exe + _internal\).
Source: "dist\receipt-board\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Receipt Board"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Receipt Board"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Code]
const
  DataSubdir = '\receipt-board';

procedure RemoveUserData();
var
  DataDir: string;
begin
  DataDir := ExpandConstant('{localappdata}') + DataSubdir;
  if DirExists(DataDir) then
  begin
    if DelTree(DataDir, True, True, True) then
      Log('Removed user data: ' + DataDir)
    else
      Log('Failed to remove user data: ' + DataDir);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: string;
begin
  if CurUninstallStep <> usPostUninstall then
    exit;

  // Never prompt or wipe during a silent/automated uninstall - this also covers an
  // in-place update (which keeps prior data so a reinstall finds it).
  if UninstallSilent() then
    exit;

  DataDir := ExpandConstant('{localappdata}') + DataSubdir;
  if not DirExists(DataDir) then
    exit;

  // Default button is No (MB_DEFBUTTON2) -> keep the data unless the user opts in.
  if MsgBox(
      'Remove Receipt Board user data and configuration too?' #13#10 #13#10
      + 'This permanently deletes ' + DataDir + ', including:' #13#10
      + '  - receipt_board.sqlite (your checklists)' #13#10
      + '  - config.toml, runtime.json, receipt-board.log' #13#10 #13#10
      + 'Choose No to keep your data for a future reinstall.',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    RemoveUserData();
end;
