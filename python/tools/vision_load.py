import base64
import httpx
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Tool, Response
from python.helpers import runtime, files, images
from mimetypes import guess_type
from python.helpers import history

# image optimization and token estimation for context window
MAX_PIXELS = 768_000
QUALITY = 75
TOKENS_ESTIMATE = 1500

# HTTP client timeout for downloading images
HTTP_TIMEOUT = 30.0


def is_url(path: str) -> bool:
    """Check if path is a URL."""
    return path.startswith("http://") or path.startswith("https://")


async def download_image(url: str) -> bytes | None:
    """Download image from URL and return bytes."""
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "image" in content_type or any(
                url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
            ):
                return response.content
            return None
    except Exception:
        return None


class VisionLoad(Tool):
    async def execute(self, paths: list[str] = [], **kwargs) -> Response:

        self.images_dict = {}
        template: list[dict[str, str]] = []  # type: ignore

        for path in paths:
            # Handle URLs
            if is_url(path):
                if path not in self.images_dict:
                    try:
                        file_content = await download_image(path)
                        if file_content:
                            # Compress and convert to JPEG
                            compressed = images.compress_image(
                                file_content, max_pixels=MAX_PIXELS, quality=QUALITY
                            )
                            # Encode as base64
                            file_content_b64 = base64.b64encode(compressed).decode("utf-8")
                            self.images_dict[path] = file_content_b64
                        else:
                            self.images_dict[path] = None
                            PrintStyle().error(f"Failed to download image from {path}")
                            self.agent.context.log.log("warning", f"Failed to download image from {path}")
                    except Exception as e:
                        self.images_dict[path] = None
                        PrintStyle().error(f"Error processing image from URL {path}: {e}")
                        self.agent.context.log.log("warning", f"Error processing image from URL {path}: {e}")
                continue

            # Handle local files
            if not await runtime.call_development_function(files.exists, str(path)):
                continue

            if path not in self.images_dict:
                mime_type, _ = guess_type(str(path))
                if mime_type and mime_type.startswith("image/"):
                    try:
                        # Read binary file
                        file_content = await runtime.call_development_function(
                            files.read_file_base64, str(path)
                        )
                        file_content = base64.b64decode(file_content)
                        # Compress and convert to JPEG
                        compressed = images.compress_image(
                            file_content, max_pixels=MAX_PIXELS, quality=QUALITY
                        )
                        # Encode as base64
                        file_content_b64 = base64.b64encode(compressed).decode("utf-8")

                        # DEBUG: Save compressed image
                        # await runtime.call_development_function(
                        #     files.write_file_base64, str(path), file_content_b64
                        # )

                        # Construct the data URL (always JPEG after compression)
                        self.images_dict[path] = file_content_b64
                    except Exception as e:
                        self.images_dict[path] = None
                        PrintStyle().error(f"Error processing image {path}: {e}")
                        self.agent.context.log.log("warning", f"Error processing image {path}: {e}")

        return Response(message="dummy", break_loop=False)

    async def after_execution(self, response: Response, **kwargs):

        # build image data messages for LLMs, or error message
        content = []
        if self.images_dict:
            for path, image in self.images_dict.items():
                if image:
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                        }
                    )
                else:
                    content.append(
                        {
                            "type": "text",
                            "text": "Error processing image " + path,
                        }
                    )
            # append as raw message content for LLMs with vision tokens estimate
            msg = history.RawMessage(raw_content=content, preview="<Base64 encoded image data>")
            self.agent.hist_add_message(
                False, content=msg, tokens=TOKENS_ESTIMATE * len(content)
            )
        else:
            self.agent.hist_add_tool_result(self.name, "No images processed")

        # print and log short version
        message = (
            "No images processed"
            if not self.images_dict
            else f"{len(self.images_dict)} images processed"
        )
        PrintStyle(
            font_color="#1B4F72", background_color="white", padding=True, bold=True
        ).print(f"{self.agent.agent_name}: Response from tool '{self.name}'")
        PrintStyle(font_color="#85C1E9").print(message)
        self.log.update(result=message)
