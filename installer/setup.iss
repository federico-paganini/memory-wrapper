[Setup]
AppId={{CD4F44C8-F6DF-4D80-85FC-0D8D0092428C}
AppName=Memory Contab
AppVersion=1.0.0
AppPublisher=Federico Paganini
DefaultDirName=C:\MemoryWrapper
DefaultGroupName=MemoryWrapper
OutputBaseFilename=MemoryWrapper_Installer
SetupIconFile=..\assets\Icon.ico
UninstallDisplayIcon={app}\assets\Icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableDirPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
; The DOS program reads AND writes its data files (*.DAT) here, and CONT.PRN is
; written here too — a non-admin runtime user must be able to write to it.
Name: "{app}\legacy\program"; Permissions: users-modify
; DOSBox-X writes captures / savestates under its own folder.
Name: "{app}\dosbox"; Permissions: users-modify

[Files]
; Wrapper
Source: "..\dist\MemoryWrapper.exe"; DestDir: "{app}"; Flags: ignoreversion

; Assets
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

; DOSBox-X (whole folder — resilient to version changes adding/renaming files)
Source: "C:\DOSBox-X\*"; DestDir: "{app}\dosbox"; Flags: ignoreversion recursesubdirs

; DOS program + data
Source: "..\legacy\program\*"; DestDir: "{app}\legacy\program"; Flags: ignoreversion recursesubdirs

; DOSBox conf
Source: "..\legacy\dosbox-x.conf"; DestDir: "{app}\legacy"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Memory Contab"; Filename: "{app}\MemoryWrapper.exe"; IconFilename: "{app}\assets\Icon.ico"

[Run]
Filename: "{app}\MemoryWrapper.exe"; Description: "Iniciar Memory Contab"; Flags: nowait postinstall skipifsilent
