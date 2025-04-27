#define MyAppName "Billing System"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Company"
#define MyAppExeName "BillingSystem.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-4A5B-8C7D-6E9F0A1B2C3D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=BillingSystem_Setup
Compression=lzma
SolidCompression=yes
CreateAppDir=yes

[Dirs]
Name: "{app}\database"; Permissions: users-full
Name: "{app}\bills"; Permissions: users-full
Name: "{app}\logs"; Permissions: users-full

[Files]
; Copy the main executable and dependencies
Source: "build\BillingSystem\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Create empty database directory with write permissions
Source: "database\*"; DestDir: "{app}\database"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "bills\*"; DestDir: "{app}\bills"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch application"; Flags: postinstall nowait