; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "ged2doc"
#define MyAppVersion "0.4.2"
#define MyAppPublisher "Andy Salnikov"
#define MyAppURL "https://github.com/andy-z/ged2doc"
#define MyAppExeName "ged2doc.exe"
#define SourceDir "..\build\exe.win32-3.8"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{A9E38633-B051-4269-AE14-CC1638B8C282}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userpf}\{#MyAppName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=ged2doc-setup-{#MyAppVersion}
SetupIconFile=setup.ico
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; InfoAfterFile: "post-install-en.txt"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"; InfoAfterFile: "post-install-ru.txt"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\ged2doc.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\python38.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\lib\*"; DestDir: "{app}\lib"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "ged2doc.ico"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{commonprograms}\{#MyAppName}"; Filename: "cmd.exe"; WorkingDir: "{userdesktop}"; Parameters: "/k {app}\start.bat"; IconFilename: "{app}\ged2doc.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "cmd.exe"; WorkingDir: "{userdesktop}"; Parameters: "/k {app}\start.bat"; IconFilename: "{app}\ged2doc.ico"; Tasks: desktopicon 

