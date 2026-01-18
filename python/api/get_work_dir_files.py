from flask import Response

from python.helpers.api import ApiHandler, Request
from python.helpers.file_browser import FileBrowser, validate_path, ALLOWED_ROOTS
from python.helpers import runtime


class GetWorkDirFiles(ApiHandler):
    @classmethod
    def get_methods(cls):
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        current_path = request.args.get("path", "")
        if current_path == "$WORK_DIR":
            current_path = "/a0"

        # Validate path before processing
        if current_path:
            # Ensure path starts with /a0 or is relative within /a0
            if not current_path.startswith("/a0"):
                current_path = f"/a0/{current_path.lstrip('/')}"

            is_valid, result = validate_path(current_path, ALLOWED_ROOTS)
            if not is_valid:
                return Response('{"error": "Invalid path: access denied"}', status=403, mimetype="application/json")

        result = await runtime.call_development_function(get_files, current_path)
        return {"data": result}


async def get_files(path):
    browser = FileBrowser()
    return browser.get_files(path)
