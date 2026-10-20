; Compile an installer from a validated one-folder bundle.
#ifndef BundleRoot
  #error BundleRoot must point to a validated AMP bundle
#endif
#ifndef OutputRoot
  #error OutputRoot is required
#endif
#ifndef AppVersion
  #define AppVersion "0.8b"
#endif
[Setup]
AppId={{DF5713F5-6E84-4EA3-9330-A510C77819DD}
AppName=AMP
AppVersion={#AppVersion}
AppVerName=AMP {#AppVersion}
AppPublisher=Wolf Forge
AppPublisherURL=https://wolf-forge.co.uk
AppSupportURL=https://github.com/DrakonWolfDev/AMP/issues
DefaultDirName={localappdata}\Programs\AMP
DefaultGroupName=AMP
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir={#OutputRoot}
OutputBaseFilename=AMP-{#AppVersion}-setup
SetupIconFile={#SourcePath}\..\..\amp\assets\amp.ico
UninstallDisplayIcon={app}\AMP.exe
LicenseFile={#BundleRoot}\_internal\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ChangesAssociations=yes
VersionInfoCompany=Wolf Forge
VersionInfoDescription=AMP installer
[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; Flags: unchecked
Name: "fileassociations"; Description: "Register AMP in Open with (keep existing defaults)"; GroupDescription: "File associations:"; Flags: unchecked
[Files]
Source: "{#BundleRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\AMP"; Filename: "{app}\AMP.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\AMP"; Filename: "{app}\AMP.exe"; WorkingDir: "{app}"; Tasks: desktopicon
[Run]
Filename: "{app}\AMP.exe"; Description: "Launch AMP"; Flags: nowait postinstall skipifsilent

#include "associations.iss"
