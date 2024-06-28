from dotenv import load_dotenv
from uuid import uuid4
import cloudinary.uploader
import cloudinary
import re

load_dotenv()

config = cloudinary.config(secure=True)


def upload_image_on_cloudinary(image_file):
    try:
        unique_id = str(uuid4())

        result = cloudinary.uploader.upload(
            image_file,
            public_id=unique_id,
            folder="uploads",
            resource_type="auto"
        )

        print("Upload result:", result["public_id"])
        return result

    except Exception as e:
        print(f"Error while file upload: {str(e)}")
        return None


def delete_image_from_cloudinary(public_uuid):
    try:
        public_id = f"uploads/{public_uuid}"
        result = cloudinary.uploader.destroy(public_id)
        print("Delete result:", result)
        if result.get("result") == "ok":
            return True
        return False
    except Exception as e:
        print(f"Error while file delete: {str(e)}")
        return False


def extract_uuid_from_url(url: str) -> str | None:
    match = re.search(r'/([a-f0-9\-]{36})\.', url)
    return match.group(1) if match else None


# print("****Cloudinary Configuration SDK:****\nCredentials:", config.cloud_name, config.api_key, "\n")
