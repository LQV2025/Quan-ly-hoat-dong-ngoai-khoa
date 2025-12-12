Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "D:\Destop\TTTN\appNK\ngrok.exe http 5000", 0, True
Set WshShell = Nothing