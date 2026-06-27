[Setup]
AppName=Memory Contab
AppVersion=0.1.0
DefaultDirName=C:\MemoryWrapper
DefaultGroupName=MemoryWrapper
OutputBaseFilename=MemoryWrapper_Installer
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableDirPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Wrapper
Source: "..\dist\MemoryWrapper.exe"; DestDir: "{app}"; Flags: ignoreversion

; Assets
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

; DOSBox-X
Source: "C:\DOSBox-X\dosbox-x.exe"; DestDir: "{app}\dosbox"; Flags: ignoreversion
Source: "C:\DOSBox-X\inpout32.dll"; DestDir: "{app}\dosbox"; Flags: ignoreversion
Source: "C:\DOSBox-X\inpoutx64.dll"; DestDir: "{app}\dosbox"; Flags: ignoreversion
Source: "C:\DOSBox-X\FREECG98.BMP"; DestDir: "{app}\dosbox"; Flags: ignoreversion
Source: "C:\DOSBox-X\Nouveau_IBM.ttf"; DestDir: "{app}\dosbox"; Flags: ignoreversion
Source: "C:\DOSBox-X\SarasaGothicFixed.ttf"; DestDir: "{app}\dosbox"; Flags: ignoreversion
Source: "C:\DOSBox-X\drivez\*"; DestDir: "{app}\dosbox\drivez"; Flags: ignoreversion recursesubdirs
Source: "C:\DOSBox-X\glshaders\*"; DestDir: "{app}\dosbox\glshaders"; Flags: ignoreversion recursesubdirs
Source: "C:\DOSBox-X\languages\*"; DestDir: "{app}\dosbox\languages"; Flags: ignoreversion recursesubdirs
Source: "C:\DOSBox-X\scripts\*"; DestDir: "{app}\dosbox\scripts"; Flags: ignoreversion recursesubdirs
Source: "C:\DOSBox-X\shaders\*"; DestDir: "{app}\dosbox\shaders"; Flags: ignoreversion recursesubdirs

; Programa DOS
Source: "..\legacy\program\*"; DestDir: "{app}\legacy\program"; Flags: ignoreversion recursesubdirs

; DOSBox conf
Source: "..\legacy\dosbox-x.conf"; DestDir: "{app}\legacy"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Memory Contab"; Filename: "{app}\MemoryWrapper.exe"; IconFilename: "{app}\assets\icon.ico"

[Run]
Filename: "{app}\MemoryWrapper.exe"; Description: "Iniciar Memory Contab"; Flags: nowait postinstall skipifsilent