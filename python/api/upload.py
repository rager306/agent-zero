import os

from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
from werkzeug.utils import secure_filename


class UploadFile(ApiHandler):
    # Maximum file size: 100MB
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # Allowed file extensions by category
    ALLOWED_EXTENSIONS = {
        # Images
        "png",
        "jpg",
        "jpeg",
        "gif",
        "bmp",
        "webp",
        "svg",
        # Documents
        "txt",
        "pdf",
        "csv",
        "html",
        "json",
        "md",
        "xml",
        "yaml",
        "yml",
        # Code files
        "py",
        "js",
        "ts",
        "css",
        "sh",
        "bash",
        # Archives
        "zip",
        "tar",
        "gz",
    }

    async def process(self, input: dict, request: Request) -> dict | Response:
        if "file" not in request.files:
            raise Exception("No file part")

        file_list = request.files.getlist("file")  # Handle multiple files
        saved_filenames = []
        failed_files = []

        for file in file_list:
            if not file or not file.filename:
                continue

            # Validate file before saving
            validation_error = self.validate_file(file)
            if validation_error:
                failed_files.append({"filename": file.filename, "error": validation_error})
                continue

            filename = secure_filename(file.filename)
            file.save(files.get_abs_path("tmp/upload", filename))
            saved_filenames.append(filename)

        if not saved_filenames and failed_files:
            errors = "; ".join([f"{f['filename']}: {f['error']}" for f in failed_files])
            raise Exception(f"All uploads failed: {errors}")

        return {
            "filenames": saved_filenames,
            "failed": failed_files,
        }

    def validate_file(self, file) -> str | None:
        """
        Validate file for size, extension, and content.
        Returns None if valid, or an error message string if invalid.
        """
        # Check for empty filename
        if not file.filename:
            return "Empty filename"

        # Check file extension
        if not self.allowed_file(file.filename):
            return f"File type not allowed. Allowed extensions: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"

        # Check file size
        size_error = self.check_file_size(file)
        if size_error:
            return size_error

        return None

    def allowed_file(self, filename: str) -> bool:
        """Check if the file extension is allowed."""
        if not filename or "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS

    def check_file_size(self, file) -> str | None:
        """
        Check if file size is within allowed limits.
        Returns None if valid, or an error message if too large.
        """
        try:
            # Get current position
            current_pos = file.tell()
            # Seek to end to get size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            # Reset to original position
            file.seek(current_pos)

            if size == 0:
                return "Empty file"
            if size > self.MAX_FILE_SIZE:
                max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                return f"File too large. Maximum size is {max_mb:.0f}MB"
            return None
        except (AttributeError, IOError) as e:
            return f"Could not determine file size: {e}"
