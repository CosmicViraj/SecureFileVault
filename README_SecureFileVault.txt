SECURE FILE VAULT
=================

What it does
------------
- Lets you select any file using a Windows desktop GUI.
- Encrypts the selected file in place with AES-256-GCM.
- Decrypts it only with the correct password.
- Creates a .backup copy before overwriting the selected file.
- Detects a wrong password or modified/corrupted encrypted file.

Run as Python
-------------
1. Install Python 3.11 or newer.
2. Open Command Prompt in this folder.
3. Run:

   python -m pip install -r requirements.txt
   python secure_file_vault.py

Build the Windows EXE
---------------------
1. Put secure_file_vault.py and build_windows_exe.bat in the same folder.
2. Double-click build_windows_exe.bat.
3. The script installs cryptography and PyInstaller.
4. When complete, find:

   dist\SecureFileVault.exe

Important
---------
- There is no password recovery. Do not forget the password.
- Test with a copy of a file before using it on important data.
- Backup files are named file.ext.backup, file.ext.backup1, etc.
- The encrypted file keeps its original filename and extension, but its contents are encrypted.
