#define MyAppName "QuiLe-Autovocal"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "QuiLe"
#define MyAppExeName "QuiLe-Autovocal.exe"

[Setup]
AppId={{B6A6A5A1-1D3C-4B2E-8D1D-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\QuiLe-Autovocal
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=QuiLe-Autovocal-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình"; GroupDescription: "Tùy chọn bổ sung:"

[Files]
Source: "dist\QuiLe-Autovocal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#ifexist "drivers\ASIO-Driver-Setup.exe"
Source: "drivers\ASIO-Driver-Setup.exe"; DestDir: "{tmp}"; Flags: ignoreversion dontcopy
#endif
Source: "drivers\README.md"; DestDir: "{app}\drivers"; Flags: ignoreversion
Source: "USER_MANUAL_VI.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{group}\QuiLe-Autovocal"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\QuiLe-Autovocal"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
#ifexist "drivers\ASIO-Driver-Setup.exe"
Filename: "{tmp}\ASIO-Driver-Setup.exe"; Description: "Cài driver ASIO đi kèm"; StatusMsg: "Đang cài driver ASIO…"; Flags: waituntilterminated
#endif
Filename: "{app}\{#MyAppExeName}"; Description: "Khởi động QuiLe-Autovocal"; Flags: nowait postinstall skipifsilent

[Code]
function HasBundledAsioDriver(): Boolean;
begin
  Result := FileExists(ExpandConstant('{src}\drivers\ASIO-Driver-Setup.exe'));
end;
