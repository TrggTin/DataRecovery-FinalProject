import os
import sys
from myfs import MyFS

def main():
    # Define volumes (ensure these paths exist or are creatable)
    volume_x_path = 'X:/MyFS.Dat'  # Main file storage
    volume_y_path = 'Y:/MyFS_Metadata.dat'  # Metadata storage

    # Check volume paths
    for path in [volume_x_path, volume_y_path]:
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            print(f"Error: Directory {directory} does not exist")
            return

    # Create MyFS instance
    myfs = MyFS(volume_x_path, volume_y_path)

    # Interactive Menu
    while True:
        print("\n--- MyFS Secure File System ---")
        print("1. Create MyFS")
        print("2. Import File")
        print("3. Dynamic Password Check")
        print("4. Change System Password")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        try:
            if choice == '1':
                system_password = input("Enter system password: ")
                myfs.create_myfs(system_password)
                print("MyFS successfully created!")

            elif choice == '2':
                # Verify dynamic password first
                if not myfs.check_dynamic_password():
                    print("Dynamic password check failed. Access denied.")
                    continue

                file_path = input("Enter full path of file to import: ")
                file_password = input("Enter optional file password (press Enter to skip): ")
                
                if file_password:
                    myfs.import_file(file_path, file_password)
                else:
                    myfs.import_file(file_path)
                print("File imported successfully!")

            elif choice == '3':
                result = myfs.check_dynamic_password()
                print("Dynamic Password Check:", "Passed" if result else "Failed")

            elif choice == '4':
                old_password = input("Enter current system password: ")
                new_password = input("Enter new system password: ")
                myfs.change_system_password(old_password, new_password)
                print("System password changed successfully!")

            elif choice == '5':
                print("Exiting MyFS...")
                break

            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()