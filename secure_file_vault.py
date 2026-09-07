import os
import shutil
import struct
import tkinter as tk
from tkinter import filedialog, messagebox

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


MAGIC = b"SFV1"
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 600_000
HEADER_STRUCT = struct.Struct(">4sI16s12s")


def derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))


def make_backup(path: str) -> str:
    backup_path = path + ".backup"
    counter = 1
    while os.path.exists(backup_path):
        backup_path = f"{path}.backup{counter}"
        counter += 1
    shutil.copy2(path, backup_path)
    return backup_path


class SecureFileVaultApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Secure File Vault")
        self.root.geometry("700x470")
        self.root.minsize(700, 470)

        self.file_path = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        self.show_password = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Select a file to begin.")

        self.build_ui()

    def build_ui(self):
        outer = tk.Frame(self.root, padx=28, pady=24)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="Secure File Vault",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            outer,
            text="Encrypt or decrypt the selected file in place using AES-256-GCM.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 22))

        tk.Label(outer, text="File", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        file_row = tk.Frame(outer)
        file_row.pack(fill="x", pady=(6, 16))

        tk.Entry(
            file_row,
            textvariable=self.file_path,
            font=("Segoe UI", 10),
        ).pack(side="left", fill="x", expand=True, ipady=7)

        tk.Button(
            file_row,
            text="Browse...",
            width=12,
            command=self.browse_file,
        ).pack(side="left", padx=(10, 0), ipady=3)

        tk.Label(outer, text="Password", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.password_entry = tk.Entry(
            outer,
            textvariable=self.password,
            show="•",
            font=("Segoe UI", 10),
        )
        self.password_entry.pack(fill="x", pady=(6, 14), ipady=7)

        tk.Label(
            outer,
            text="Confirm password (required when encrypting)",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        self.confirm_entry = tk.Entry(
            outer,
            textvariable=self.confirm_password,
            show="•",
            font=("Segoe UI", 10),
        )
        self.confirm_entry.pack(fill="x", pady=(6, 8), ipady=7)

        tk.Checkbutton(
            outer,
            text="Show password",
            variable=self.show_password,
            command=self.toggle_password_visibility,
        ).pack(anchor="w", pady=(0, 18))

        button_row = tk.Frame(outer)
        button_row.pack(fill="x", pady=(0, 18))

        tk.Button(
            button_row,
            text="Encrypt File",
            command=self.encrypt_file,
            font=("Segoe UI", 10, "bold"),
            height=2,
        ).pack(side="left", fill="x", expand=True, padx=(0, 7))

        tk.Button(
            button_row,
            text="Decrypt File",
            command=self.decrypt_file,
            font=("Segoe UI", 10, "bold"),
            height=2,
        ).pack(side="left", fill="x", expand=True, padx=(7, 0))

        tk.Label(
            outer,
            textvariable=self.status,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=630,
        ).pack(fill="x", pady=(4, 10))

        tk.Label(
            outer,
            text=(
                "Important: Keep your password safe. There is no password recovery. "
                "A .backup copy is created before the original file is overwritten."
            ),
            font=("Segoe UI", 9, "italic"),
            justify="left",
            wraplength=630,
        ).pack(anchor="w")

    def browse_file(self):
        path = filedialog.askopenfilename(title="Select a file")
        if path:
            self.file_path.set(path)
            self.status.set(f"Selected: {path}")

    def toggle_password_visibility(self):
        char = "" if self.show_password.get() else "•"
        self.password_entry.config(show=char)
        self.confirm_entry.config(show=char)

    def get_valid_path(self):
        path = self.file_path.get().strip().strip('"').strip("'")
        if not path:
            messagebox.showwarning("No file selected", "Please choose a file first.")
            return None
        if not os.path.isfile(path):
            messagebox.showerror("File not found", "The selected file does not exist.")
            return None
        return path

    def encrypt_file(self):
        path = self.get_valid_path()
        if not path:
            return

        password = self.password.get()
        confirmation = self.confirm_password.get()

        if len(password) < 8:
            messagebox.showwarning(
                "Weak password",
                "Use a password with at least 8 characters.",
            )
            return

        if password != confirmation:
            messagebox.showwarning(
                "Passwords do not match",
                "Password and confirmation must match.",
            )
            return

        try:
            with open(path, "rb") as f:
                plaintext = f.read()

            if plaintext.startswith(MAGIC):
                if not messagebox.askyesno(
                    "Already encrypted?",
                    "This file starts with the Secure File Vault header. Encrypt it again anyway?",
                ):
                    return

            salt = os.urandom(SALT_SIZE)
            nonce = os.urandom(NONCE_SIZE)
            key = derive_key(password, salt, PBKDF2_ITERATIONS)
            aesgcm = AESGCM(key)

            header = HEADER_STRUCT.pack(MAGIC, PBKDF2_ITERATIONS, salt, nonce)
            ciphertext = aesgcm.encrypt(nonce, plaintext, header)
            encrypted_blob = header + ciphertext

            backup_path = make_backup(path)

            with open(path, "wb") as f:
                f.write(encrypted_blob)

            self.status.set(f"Encrypted successfully. Backup: {backup_path}")
            self.confirm_password.set("")
            messagebox.showinfo(
                "Encryption complete",
                f"The file was encrypted successfully.\n\nBackup created:\n{backup_path}",
            )
        except Exception as exc:
            messagebox.showerror("Encryption failed", f"Could not encrypt the file.\n\n{exc}")

    def decrypt_file(self):
        path = self.get_valid_path()
        if not path:
            return

        password = self.password.get()
        if not password:
            messagebox.showwarning("Password required", "Enter the encryption password.")
            return

        try:
            with open(path, "rb") as f:
                blob = f.read()

            if len(blob) < HEADER_STRUCT.size + 16:
                raise ValueError("The file is too small to be a Secure File Vault file.")

            header = blob[:HEADER_STRUCT.size]
            magic, iterations, salt, nonce = HEADER_STRUCT.unpack(header)

            if magic != MAGIC:
                raise ValueError("This file was not encrypted by Secure File Vault.")

            if iterations < 100_000 or iterations > 5_000_000:
                raise ValueError("The encrypted file contains an invalid key-derivation setting.")

            ciphertext = blob[HEADER_STRUCT.size:]
            key = derive_key(password, salt, iterations)
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, header)

            backup_path = make_backup(path)

            with open(path, "wb") as f:
                f.write(plaintext)

            self.status.set(f"Decrypted successfully. Backup: {backup_path}")
            self.confirm_password.set("")
            messagebox.showinfo(
                "Decryption complete",
                f"The file was decrypted successfully.\n\nBackup created:\n{backup_path}",
            )
        except InvalidTag:
            messagebox.showerror(
                "Decryption failed",
                "Wrong password, corrupted file, or the encrypted file was modified.",
            )
        except Exception as exc:
            messagebox.showerror("Decryption failed", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureFileVaultApp(root)
    root.mainloop()
