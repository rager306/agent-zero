import base64
from werkzeug.datastructures import FileStorage
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.file_browser import FileBrowser
from python.helpers import runtime
from python.api import get_work_dir_files


class UploadWorkDirFiles(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if "files[]" not in request.files:
            raise Exception("No files uploaded")

        current_path = request.form.get("path", "")
        uploaded_files = request.files.getlist("files[]")

        successful, failed = await upload_files(uploaded_files, current_path)

        if not successful and failed:
            # Collect failure reasons for better error messages
            failure_details = "; ".join([f"{name}: {reason}" for name, reason in failed])
            raise Exception(f"All uploads failed: {failure_details}")

        result = await runtime.call_development_function(get_work_dir_files.get_files, current_path)

        return {
            "message": ("Files uploaded successfully" if not failed else "Some files failed to upload"),
            "data": result,
            "successful": successful,
            "failed": [name for name, _ in failed] if failed else [],
            "failed_details": [{"filename": name, "reason": reason} for name, reason in failed] if failed else [],
        }


async def upload_files(uploaded_files: list[FileStorage], current_path: str) -> tuple[list[str], list[tuple[str, str]]]:
    """
    Upload files with server-side validation.
    Returns (successful_filenames, failed_files_with_reasons).
    """
    browser = FileBrowser()
    successful: list[str] = []
    failed: list[tuple[str, str]] = []

    if runtime.is_development():
        for file in uploaded_files:
            if not file or not file.filename:
                failed.append(("unknown", "No filename provided"))
                continue

            # Read file content
            try:
                file_content = file.stream.read()
            except Exception as e:
                failed.append((file.filename, f"Failed to read file: {e}"))
                continue

            # Validate before sending to development environment
            is_valid, error = browser._validate_upload(file.filename, content_bytes=file_content)
            if not is_valid:
                failed.append((file.filename, error or "Validation failed"))
                continue

            base64_content = base64.b64encode(file_content).decode("utf-8")
            if await runtime.call_development_function(upload_file, current_path, file.filename, base64_content):
                successful.append(file.filename)
            else:
                failed.append((file.filename, "Failed to save file"))
    else:
        # Use FileBrowser.save_files which now includes validation
        success_list, fail_list = browser.save_files(uploaded_files, current_path)
        successful = success_list
        # Convert failed filenames to tuples with generic reason
        # (detailed reasons are logged by FileBrowser)
        failed = [(name, "Upload validation or save failed") for name in fail_list]

    return successful, failed


async def upload_file(current_path: str, filename: str, base64_content: str) -> bool:
    """
    Save a base64-encoded file in the development environment.
    FileBrowser.save_file_b64 now includes full validation.
    """
    browser = FileBrowser()
    return browser.save_file_b64(current_path, filename, base64_content)
