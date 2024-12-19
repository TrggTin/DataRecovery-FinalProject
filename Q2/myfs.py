import os
import hashlib
import secrets
import struct
import json
import uuid
import time
import random
import shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

class SmartOTP:
    @staticmethod
    def generate_otp(x):
        """Generate 8-digit OTP based on 4-digit input X"""
        # Simulating a complex OTP generation mechanism
        random.seed(x)
        # Complex transformation to make output look random
        y = int(''.join([str(random.randint(0,9)) for _ in range(8)]))
        return y

class MyFSMetadata:
    def __init__(self):
        self.computer_id = str(uuid.getnode())
        self.creation_time = time.time()
        self.files = {}
        self.system_password = None

class MyFS:
    def __init__(self, volume_x_path, volume_y_path):
        self.volume_x_path = volume_x_path  # MyFS.Dat location
        self.volume_y_path = volume_y_path  # Metadata location
        self.max_files = 99
        self.max_file_size = 4 * 1024 * 1024 * 1024  # 4GB
        self.metadata = None

    def _generate_encryption_key(self, password):
        """Generate a secure encryption key from password"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        # bytes arent json serializable, so we have to convert them to string for storage
        # when using them in Fernet, use base64.b64decode(key) to convert back to bytes
        return base64.b64encode(key).decode('utf-8'), base64.b64encode(salt).decode('utf-8')

    def _verify_computer(self):
        """Verify if current computer matches the one that created the file system"""
        if not self.metadata:
            raise ValueError("MyFS not initialized")
        return str(uuid.getnode()) == self.metadata.computer_id

    def create_myfs(self, system_password):
        """Create MyFS volume with initial metadata"""
        if os.path.exists(self.volume_x_path) or os.path.exists(self.volume_y_path):
            raise FileExistsError("MyFS volumes already exist")

        # Create empty files
        open(self.volume_x_path, 'wb').close()
        open(self.volume_y_path, 'wb').close()

        # Generate metadata
        metadata = MyFSMetadata()
        print(json.dumps(metadata.__dict__))
        key, salt = self._generate_encryption_key(system_password)
        metadata.system_password = {
            'salt': salt,
            'key': key
        }

        # Encrypt and save metadata
        fernet = Fernet(base64.b64decode(key))
        encrypted_metadata = fernet.encrypt(json.dumps(metadata.__dict__).encode())
        
        with open(self.volume_y_path, 'wb') as f:
            f.write(encrypted_metadata)

        self.metadata = metadata
        return True

    def change_system_password(self, old_password, new_password):
        """Change system-level password"""
        if not self._verify_computer():
            raise PermissionError("Unauthorized computer")

        # Decrypt existing metadata
        current_metadata = self._load_metadata(old_password)
        
        # Generate new encryption key
        new_key, new_salt = self._generate_encryption_key(new_password)
        current_metadata['system_password'] = {
            'salt': new_salt,
            'key': new_key
        }

        # Re-encrypt and save
        fernet = Fernet(new_key)
        encrypted_metadata = fernet.encrypt(json.dumps(current_metadata).encode())
        
        with open(self.volume_y_path, 'wb') as f:
            f.write(encrypted_metadata)

    def import_file(self, file_path, file_password=None):
        """Import a file into MyFS"""
        if not self._verify_computer():
            raise PermissionError("Unauthorized computer")

        if len(self.metadata.files) >= self.max_files:
            raise ValueError("MyFS volume is full")

        file_stats = os.stat(file_path)
        
        if file_stats.st_size > self.max_file_size:
            print(f"Warning: Large file {file_path} might have limited protection")

        # File metadata
        file_metadata = {
            'original_path': file_path,
            'import_time': time.time(),
            'size': file_stats.st_size,
            'has_password': bool(file_password)
        }

        # Encrypt file content if password provided
        with open(file_path, 'rb') as f:
            file_content = f.read()

        if file_password:
            file_key, file_salt = self._generate_encryption_key(file_password)
            fernet = Fernet(file_key)
            file_content = fernet.encrypt(file_content)
            file_metadata['file_salt'] = file_salt

        # Save encrypted file in MyFS.Dat
        with open(self.volume_x_path, 'ab') as f:
            file_offset = f.tell()
            f.write(file_content)

        # Update file metadata
        file_metadata['offset'] = file_offset
        self.metadata.files[os.path.basename(file_path)] = file_metadata

        return True

    def _detect_tampering(self):
        """Detect potential system tampering"""
        # Implement checks for unexpected modifications
        pass

    def check_dynamic_password(self):
        """Dynamic password verification mechanism"""
        x = random.randint(1000, 9999)  # 4-digit number
        print(f"Enter the matching 8-digit OTP for {x}")
        
        start_time = time.time()
        attempts = 0
        
        while attempts < 3:
            try:
                user_input = input("Enter OTP: ")
                elapsed_time = time.time() - start_time
                
                if elapsed_time > 20:
                    print("Time expired. Access denied.")
                    return False
                
                expected_otp = SmartOTP.generate_otp(x)
                if int(user_input) == expected_otp:
                    return True
                
                attempts += 1
                print(f"Incorrect OTP. {3 - attempts} attempts remaining.")
            
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        return False

def main():
    # Example usage
    myfs = MyFS('X:/MyFS.Dat', 'Y:/MyFS_Metadata.dat')
    
    # Initialize system
    myfs.create_myfs('initial_system_password')
    
    # Dynamic password check
    if not myfs.check_dynamic_password():
        print("System will now self-terminate.")
        return
    
    # Import a file
    myfs.import_file('/path/to/important/file.txt', 'optional_file_password')

if __name__ == "__main__":
    main()

__all__ = ['MyFS', 'SmartOTP']