; Inno Setup 6 script for the Windows installer (KD-packaging-pyinstaller, architecture
; section 7). Build with packaging/build_windows.ps1, which passes AppVersion and
; SourceDir; do not compile this file by hand.
;
; Installs for the current user only (no administrator prompt) under
; %LOCALAPPDATA%\Programs. The data folder (%LOCALAPPDATA%\USPTO Patent Intelligence,
; architecture 8.2.6) is separate, so uninstalling or updating never touches imported data.

#define AppName "USPTO Patent Intelligence"
#define AppExe AppName + ".exe"

#ifndef AppVersion
  #error AppVersion is not defined. Build with packaging/build_windows.ps1.
#endif
#ifndef SourceDir
  #error SourceDir is not defined. Build with packaging/build_windows.ps1.
#endif

[Setup]
; AppId identifies the installed app across versions, so updates replace it in place.
; Never change it.
AppId={{1D5C2ACC-6C75-461F-83B2-2CF475194CEC}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=COSC 40943 Team 06
VersionInfoVersion={#AppVersion}
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
DefaultGroupName={#AppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=..\dist
OutputBaseFilename=USPTO-Patent-Intelligence-{#AppVersion}-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
