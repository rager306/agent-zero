from flask import Response

from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.file_browser import FileBrowser, validate_path, ALLOWED_ROOTS
from python.helpers import runtime
from python.api import get_work_dir_files


class DeleteWorkDirFile(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        file_path = input.get("path", "")
        if not file_path:
            return Response('{"error": "No file path provided"}', status=400, mimetype="application/json")
        if not file_path.startswith("/"):
            file_path = f"/{file_path}"

        # Validate path is within allowed directories
        is_valid, result = validate_path(file_path, ALLOWED_ROOTS)
        if not is_valid:
            return Response('{"error": "Invalid path: access denied"}', status=403, mimetype="application/json")

        current_path = input.get("currentPath", "")

        res = await runtime.call_development_function(delete_file, file_path)

        if res:
            # Get updated file list
            result = await runtime.call_development_function(get_work_dir_files.get_files, current_path)
            return {"data": result}
        else:
            raise Exception("File not found or could not be deleted")


async def delete_file(file_path: str):
    browser = FileBrowser()
    return browser.delete_file(file_path)
