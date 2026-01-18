import os
from pathlib import Path
import shutil
import base64
import subprocess
from typing import Dict, List, Tuple, Any
from werkzeug.utils import secure_filename
from datetime import datetime

from python.helpers.print_style import PrintStyle


# Allowed root directories for file operations
ALLOWED_ROOTS = ["/a0"]


def validate_path(path: str, allowed_roots: list[str] | None = None) -> tuple[bool, str]:
    """
    Validate that a path is within allowed directories.

    Args:
        path: The path to validate (can be relative or absolute)
        allowed_roots: List of allowed root directories. Defaults to ALLOWED_ROOTS.

    Returns:
        Tuple of (is_valid, resolved_path or error_message)
    """
    if allowed_roots is None:
        allowed_roots = ALLOWED_ROOTS

    try:
        # Resolve the path to get the canonical absolute path
        resolved = Path(path).resolve()
        resolved_str = str(resolved)

        # Check if the resolved path starts with any allowed root
        for root in allowed_roots:
            root_resolved = str(Path(root).resolve())
            # Use os.path.commonpath to handle edge cases properly
            try:
                common = os.path.commonpath([resolved_str, root_resolved])
                if common == root_resolved:
                    return True, resolved_str
            except ValueError:
                # Paths on different drives (Windows) or other issues
                continue

        return False, f"Path '{path}' is outside allowed directories: {allowed_roots}"
    except Exception as e:
        return False, f"Invalid path '{path}': {e}"


def get_validated_path(path: str, allowed_roots: list[str] | None = None) -> str:
    """
    Validate and return the resolved path, or raise ValueError if invalid.

    Args:
        path: The path to validate
        allowed_roots: List of allowed root directories

    Returns:
        The resolved absolute path if valid

    Raises:
        ValueError: If the path is outside allowed directories
    """
    is_valid, result = validate_path(path, allowed_roots)
    if not is_valid:
        raise ValueError(result)
    return result


class FileBrowser:
    ALLOWED_EXTENSIONS = {
        "image": {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"},
        "code": {"py", "js", "ts", "sh", "bash", "html", "css", "json", "yaml", "yml"},
        "document": {"md", "pdf", "txt", "csv", "xml"},
        "archive": {"zip", "tar", "gz"},
    }

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self):
        # Base directory for file operations - restricted to /a0
        base_dir = "/a0"
        self.base_dir = Path(base_dir)
        self._allowed_roots = [str(self.base_dir)]

    def _validate_path(self, path: str) -> str:
        """
        Validate that a path is within allowed directories.

        Args:
            path: The path to validate (relative to base_dir or absolute)

        Returns:
            The resolved absolute path if valid

        Raises:
            ValueError: If the path is outside allowed directories
        """
        # Handle paths relative to base_dir
        if not Path(path).is_absolute():
            full_path = self.base_dir / path
        else:
            full_path = Path(path)

        return get_validated_path(str(full_path), self._allowed_roots)

    def _check_file_size(self, file) -> Tuple[bool, str | None]:
        """
        Check if file size is within allowed limits.
        Returns (is_valid, error_message).
        """
        try:
            current_pos = file.tell()
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(current_pos)

            if size == 0:
                return False, "Empty file"
            if size > self.MAX_FILE_SIZE:
                max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"File too large. Maximum size is {max_mb:.0f}MB"
            return True, None
        except (AttributeError, IOError) as e:
            return False, f"Could not determine file size: {e}"

    def _check_file_size_bytes(self, content: bytes) -> Tuple[bool, str | None]:
        """
        Check if byte content size is within allowed limits.
        Returns (is_valid, error_message).
        """
        size = len(content)
        if size == 0:
            return False, "Empty file"
        if size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large. Maximum size is {max_mb:.0f}MB"
        return True, None

    def _is_allowed_extension(self, filename: str) -> Tuple[bool, str | None]:
        """
        Check if file extension is allowed.
        Returns (is_valid, error_message).
        """
        if not filename:
            return False, "Empty filename"

        ext = self._get_file_extension(filename)
        if not ext:
            return False, "File has no extension"

        all_allowed = set().union(*self.ALLOWED_EXTENSIONS.values())
        if ext not in all_allowed:
            return False, f"File type '.{ext}' not allowed"

        return True, None

    def _validate_upload(self, filename: str, file=None, content_bytes: bytes | None = None) -> Tuple[bool, str | None]:
        """
        Validate an upload for extension and size.
        Pass either file (file-like object) or content_bytes.
        Returns (is_valid, error_message).
        """
        # Check extension
        ext_valid, ext_error = self._is_allowed_extension(filename)
        if not ext_valid:
            return False, ext_error

        # Check size
        if content_bytes is not None:
            size_valid, size_error = self._check_file_size_bytes(content_bytes)
        elif file is not None:
            size_valid, size_error = self._check_file_size(file)
        else:
            return False, "No file content provided"

        if not size_valid:
            return False, size_error

        return True, None

    def save_file_b64(self, current_path: str, filename: str, base64_content: str) -> bool:
        """
        Save a base64-encoded file with validation.
        Returns True on success, False on failure.
        """
        try:
            # Decode content first to validate size
            try:
                content_bytes = base64.b64decode(base64_content)
            except Exception as e:
                PrintStyle.error(f"Invalid base64 content for {filename}: {e}")
                return False

            # Validate upload (extension and size)
            is_valid, error = self._validate_upload(filename, content_bytes=content_bytes)
            if not is_valid:
                PrintStyle.error(f"Upload validation failed for {filename}: {error}")
                return False

            # Sanitize filename and validate path
            safe_filename = secure_filename(filename)
            if not safe_filename:
                raise ValueError("Invalid filename")

            # Build and validate the target path
            target_path = str(self.base_dir / current_path / safe_filename)
            validated_path = self._validate_path(target_path)

            os.makedirs(os.path.dirname(validated_path), exist_ok=True)
            # Save file
            with open(validated_path, "wb") as file:
                file.write(content_bytes)
            return True
        except ValueError as e:
            PrintStyle.error(f"Path validation error for {filename}: {e}")
            return False
        except Exception as e:
            PrintStyle.error(f"Error saving file {filename}: {e}")
            return False

    def save_files(self, files: List, current_path: str = "") -> Tuple[List[str], List[str]]:
        """Save uploaded files and return successful and failed filenames"""
        successful = []
        failed = []

        try:
            # Validate the target directory path
            target_dir_path = str(self.base_dir / current_path)
            validated_dir = self._validate_path(target_dir_path)

            os.makedirs(validated_dir, exist_ok=True)

            for file in files:
                try:
                    if not file or not file.filename:
                        failed.append(getattr(file, "filename", "unknown"))
                        continue

                    # Validate upload (extension and size)
                    is_valid, error = self._validate_upload(file.filename, file=file)
                    if not is_valid:
                        PrintStyle.error(f"Upload validation failed for {file.filename}: {error}")
                        failed.append(file.filename)
                        continue

                    filename = secure_filename(file.filename)
                    if not filename:
                        failed.append(file.filename)
                        continue

                    # Validate full file path
                    file_path = os.path.join(validated_dir, filename)
                    validated_file_path = self._validate_path(file_path)

                    file.save(validated_file_path)
                    successful.append(filename)

                except ValueError as e:
                    PrintStyle.error(f"Path validation error for {file.filename}: {e}")
                    failed.append(file.filename)
                except Exception as e:
                    PrintStyle.error(f"Error saving file {file.filename}: {e}")
                    failed.append(file.filename)

            return successful, failed

        except ValueError as e:
            PrintStyle.error(f"Path validation error: {e}")
            return successful, failed
        except Exception as e:
            PrintStyle.error(f"Error in save_files: {e}")
            return successful, failed

    def delete_file(self, file_path: str) -> bool:
        """Delete a file or empty directory"""
        try:
            # Validate the path using secure path validation
            validated_path = self._validate_path(file_path)

            if os.path.exists(validated_path):
                if os.path.isfile(validated_path):
                    os.remove(validated_path)
                elif os.path.isdir(validated_path):
                    shutil.rmtree(validated_path)
                return True

            return False

        except ValueError as e:
            PrintStyle.error(f"Path validation error for {file_path}: {e}")
            return False
        except Exception as e:
            PrintStyle.error(f"Error deleting {file_path}: {e}")
            return False

    def _is_allowed_file(self, filename: str, file) -> bool:
        """
        Check if a file is allowed to be uploaded.
        Validates extension and size.
        """
        is_valid, error = self._validate_upload(filename, file=file)
        if not is_valid:
            PrintStyle.error(f"File validation failed for {filename}: {error}")
            return False
        return True

    def _get_file_extension(self, filename: str) -> str:
        return filename.rsplit(".", 1)[1].lower() if "." in filename else ""

    def _get_files_via_ls(self, full_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get files and folders using ls command for better error handling"""
        files: List[Dict[str, Any]] = []
        folders: List[Dict[str, Any]] = []

        try:
            # Use ls command to get directory listing
            result = subprocess.run(
                ["ls", "-la", str(full_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                PrintStyle.error(f"ls command failed: {result.stderr}")
                return files, folders

            # Parse ls output (skip first line which is "total X")
            lines = result.stdout.strip().split("\n")
            if len(lines) <= 1:
                return files, folders

            for line in lines[1:]:  # Skip the "total" line
                try:
                    # Skip current and parent directory entries
                    if line.endswith(" .") or line.endswith(" .."):
                        continue

                    # Parse ls -la output format
                    parts = line.split()
                    if len(parts) < 9:
                        continue

                    # Check if this is a symlink (permissions start with 'l')
                    permissions = parts[0]
                    is_symlink = permissions.startswith("l")

                    if is_symlink:
                        # For symlinks, extract the name before the '->' arrow
                        full_name_part = " ".join(parts[8:])
                        if " -> " in full_name_part:
                            filename = full_name_part.split(" -> ")[0]
                            symlink_target = full_name_part.split(" -> ")[1]
                        else:
                            filename = full_name_part
                            symlink_target = None
                    else:
                        filename = " ".join(parts[8:])  # Handle filenames with spaces
                        symlink_target = None

                    if not filename:
                        continue

                    # Get full path for this entry
                    entry_path = full_path / filename

                    try:
                        stat_info = entry_path.stat()

                        entry_data: Dict[str, Any] = {
                            "name": filename,
                            "path": str(entry_path.relative_to(self.base_dir)),
                            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        }

                        # Add symlink information if this is a symlink
                        if is_symlink and symlink_target:
                            entry_data["symlink_target"] = symlink_target
                            entry_data["is_symlink"] = True

                        if entry_path.is_file():
                            entry_data.update(
                                {
                                    "type": self._get_file_type(filename),
                                    "size": stat_info.st_size,
                                    "is_dir": False,
                                }
                            )
                            files.append(entry_data)
                        elif entry_path.is_dir():
                            entry_data.update(
                                {
                                    "type": "folder",
                                    "size": 0,  # Directories show as 0 bytes
                                    "is_dir": True,
                                }
                            )
                            folders.append(entry_data)

                    except (OSError, PermissionError, FileNotFoundError) as e:
                        # Log error but continue with other files
                        PrintStyle.warning(f"No access to {filename}: {e}")
                        continue

                    if len(files) + len(folders) > 10000:
                        break

                except Exception as e:
                    # Log error and continue with next line
                    PrintStyle.error(f"Error parsing ls line '{line}': {e}")
                    continue

        except subprocess.TimeoutExpired:
            PrintStyle.error("ls command timed out")
        except Exception as e:
            PrintStyle.error(f"Error running ls command: {e}")

        return files, folders

    def get_files(self, current_path: str = "") -> Dict:
        try:
            # Validate the path using secure path validation
            full_path_str = str(self.base_dir / current_path)
            validated_path = self._validate_path(full_path_str)
            full_path = Path(validated_path)

            # Use ls command instead of os.scandir for better error handling
            files, folders = self._get_files_via_ls(full_path)

            # Combine folders and files, folders first
            all_entries = folders + files

            # Get parent directory path if not at root
            parent_path = ""
            if current_path:
                try:
                    # Get the absolute path of current directory
                    current_abs = (self.base_dir / current_path).resolve()

                    # parent_path is empty only if we're already at root
                    if str(current_abs) != str(self.base_dir):
                        parent_path = str(Path(current_path).parent)

                except Exception:
                    parent_path = ""

            return {
                "entries": all_entries,
                "current_path": current_path,
                "parent_path": parent_path,
            }

        except Exception as e:
            PrintStyle.error(f"Error reading directory: {e}")
            return {"entries": [], "current_path": "", "parent_path": ""}

    def get_full_path(self, file_path: str, allow_dir: bool = False) -> str:
        """Get full file path if it exists and is within allowed directories"""
        # Build the full path
        if Path(file_path).is_absolute():
            full_path = file_path
        else:
            full_path = str(self.base_dir / file_path)

        # Validate the path is within allowed directories
        validated_path = self._validate_path(full_path)

        if not os.path.exists(validated_path):
            raise ValueError(f"File {file_path} not found")
        return validated_path

    def _get_file_type(self, filename: str) -> str:
        ext = self._get_file_extension(filename)
        for file_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return "unknown"
