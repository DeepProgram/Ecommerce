"""
Cloudinary utility functions for uploading images and videos
"""
import cloudinary
import cloudinary.uploader
from typing import Optional, Dict, Any
import io


def upload_image_to_cloudinary(
    image_bytes: bytes,
    public_id: Optional[str] = None,
    folder: Optional[str] = "products",
    **kwargs
) -> Dict[str, Any]:
    """
    Upload processed image bytes to Cloudinary.
    
    Args:
        image_bytes: Processed image bytes (should be WebP format, 800x800, 1:1 ratio)
        public_id: Optional public ID for the image. If not provided, Cloudinary generates one.
        folder: Folder path in Cloudinary (default: "products")
        **kwargs: Additional Cloudinary upload options
    
    Returns:
        Dictionary containing Cloudinary response with 'secure_url', 'public_id', etc.
    
    Raises:
        Exception: If upload fails
    """
    try:
        upload_options = {
            "resource_type": "image",
            "folder": folder,
            **kwargs
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        # Upload from bytes
        result = cloudinary.uploader.upload(
            image_bytes,
            **upload_options
        )
        
        return result
    except Exception as e:
        raise Exception(f"Failed to upload image to Cloudinary: {str(e)}")


def upload_video_to_cloudinary(
    video_file: io.BytesIO,
    public_id: Optional[str] = None,
    folder: Optional[str] = "products/videos",
    eager: Optional[list] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Upload video file to Cloudinary.
    
    Args:
        video_file: Video file (BytesIO or file-like object)
        public_id: Optional public ID for the video. If not provided, Cloudinary generates one.
        folder: Folder path in Cloudinary (default: "products/videos")
        eager: List of transformations to generate eagerly (e.g., thumbnail generation)
        **kwargs: Additional Cloudinary upload options
    
    Returns:
        Dictionary containing Cloudinary response with 'secure_url', 'duration', 'format', etc.
    
    Raises:
        Exception: If upload fails
    """
    try:
        upload_options = {
            "resource_type": "video",
            "folder": folder,
            **kwargs
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        # Generate thumbnail eagerly if not provided
        if eager is None:
            eager = [
                {"format": "jpg", "width": 800, "height": 800, "crop": "fill"}
            ]
        
        upload_options["eager"] = eager
        
        # Upload video
        result = cloudinary.uploader.upload(
            video_file,
            **upload_options
        )
        
        return result
    except Exception as e:
        raise Exception(f"Failed to upload video to Cloudinary: {str(e)}")


def upload_large_video_to_cloudinary(
    video_file: io.BytesIO,
    public_id: Optional[str] = None,
    folder: Optional[str] = "products/videos",
    **kwargs
) -> Dict[str, Any]:
    """
    Upload large video file to Cloudinary using upload_large method.
    Use this for videos larger than 100MB.
    
    Args:
        video_file: Video file (BytesIO or file-like object)
        public_id: Optional public ID for the video
        folder: Folder path in Cloudinary (default: "products/videos")
        **kwargs: Additional Cloudinary upload options
    
    Returns:
        Dictionary containing Cloudinary response
    
    Raises:
        Exception: If upload fails
    """
    try:
        upload_options = {
            "resource_type": "video",
            "folder": folder,
            **kwargs
        }
        
        if public_id:
            upload_options["public_id"] = public_id
        
        # Upload large video
        result = cloudinary.uploader.upload_large(
            video_file,
            **upload_options
        )
        
        return result
    except Exception as e:
        raise Exception(f"Failed to upload large video to Cloudinary: {str(e)}")


def delete_from_cloudinary(
    public_id: str,
    resource_type: str = "image"
) -> Dict[str, Any]:
    """
    Delete a resource from Cloudinary.
    
    Args:
        public_id: Public ID of the resource to delete
        resource_type: Type of resource ("image" or "video")
    
    Returns:
        Dictionary containing deletion result
    
    Raises:
        Exception: If deletion fails
    """
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type
        )
        return result
    except Exception as e:
        raise Exception(f"Failed to delete resource from Cloudinary: {str(e)}")


def extract_cloudinary_public_id(url: str) -> Optional[str]:
    """
    Extract public_id from a Cloudinary URL.
    
    Args:
        url: Cloudinary URL
    
    Returns:
        Public ID if found, None otherwise
    """
    try:
        # Cloudinary URLs typically have format:
        # https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{version}/{public_id}.{format}
        parts = url.split("/upload/")
        if len(parts) > 1:
            # Remove version if present and get public_id
            public_id_part = parts[-1]
            # Remove file extension
            public_id = public_id_part.rsplit(".", 1)[0]
            return public_id
        return None
    except Exception:
        return None

