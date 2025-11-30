"""
Cloudinary utility functions for uploading images and videos.

Image Size Strategy:
- Upload one large image (max 1200px) to Cloudinary
- Use URL transformations to generate different sizes on-demand
- No need to store multiple versions - Cloudinary generates them automatically

Example Usage:
    from app.utils.cloudinary_utils import get_image_sizes, get_image_url_with_transformation
    
    # Get all common sizes
    sizes = get_image_sizes(image_url)
    thumbnail = sizes['thumbnail']  # 200px width
    medium = sizes['medium']        # 600px width
    large = sizes['large']          # 1200px width
    
    # Or generate custom size
    custom = get_image_url_with_transformation(image_url, width=400, height=400, crop="fill")
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
        image_bytes: Processed image bytes (should be WebP/JPEG format, smart cropped, no white padding)
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


def get_image_url_with_transformation(
    original_url: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    crop: str = "limit",
    quality: str = "auto",
    format: Optional[str] = None
) -> str:
    """
    Generate a Cloudinary URL with transformations for on-demand image resizing.
    This allows you to request different sizes without storing multiple versions.
    
    Args:
        original_url: Original Cloudinary URL
        width: Target width in pixels (optional)
        height: Target height in pixels (optional)
        crop: Crop mode - "limit" (default, preserves aspect ratio), 
              "fill", "fit", "scale", "crop", "thumb"
        quality: Image quality - "auto" (default), "best", "good", "eco", "low"
        format: Output format - None (keeps original), "webp", "jpg", "png", etc.
    
    Returns:
        Transformed Cloudinary URL
    
    Examples:
        # Thumbnail (200px width, auto height, preserves aspect ratio)
        thumbnail_url = get_image_url_with_transformation(url, width=200)
        
        # Medium size (600px width)
        medium_url = get_image_url_with_transformation(url, width=600)
        
        # Square thumbnail (200x200, cropped)
        square_thumb = get_image_url_with_transformation(url, width=200, height=200, crop="fill")
    """
    try:
        # Cloudinary URL format:
        # https://res.cloudinary.com/{cloud_name}/image/upload/{version}/{public_id}.{format}
        # With transformations:
        # https://res.cloudinary.com/{cloud_name}/image/upload/{transformations}/{version}/{public_id}.{format}
        
        if "/image/upload/" not in original_url:
            # Not a Cloudinary URL, return as-is
            return original_url
        
        # Split URL to insert transformations
        parts = original_url.split("/image/upload/")
        if len(parts) != 2:
            return original_url
        
        base_url = parts[0]
        rest = parts[1]
        
        # Build transformation string
        transformations = []
        if width:
            transformations.append(f"w_{width}")
        if height:
            transformations.append(f"h_{height}")
        if crop:
            transformations.append(f"c_{crop}")
        if quality:
            transformations.append(f"q_{quality}")
        if format:
            transformations.append(f"f_{format}")
        
        # If no transformations, return original
        if not transformations:
            return original_url
        
        transformation_str = ",".join(transformations)
        
        # Insert transformation before the version/public_id
        # Format: /image/upload/{transformations}/{rest}
        new_url = f"{base_url}/image/upload/{transformation_str}/{rest}"
        
        return new_url
    except Exception:
        # If transformation fails, return original URL
        return original_url


def get_image_sizes(url: str) -> dict:
    """
    Generate URLs for common image sizes using Cloudinary transformations.
    Returns a dictionary with thumbnail, medium, and large URLs.
    
    Args:
        url: Original Cloudinary image URL
    
    Returns:
        Dictionary with keys: 'thumbnail', 'medium', 'large', 'original'
        Each contains the transformed URL
    
    Usage:
        sizes = get_image_sizes(image_url)
        # Use sizes['thumbnail'] for product listings
        # Use sizes['medium'] for product detail pages
        # Use sizes['large'] for zoom/lightbox
    """
    return {
        "thumbnail": get_image_url_with_transformation(url, width=200, crop="limit", quality="auto"),
        "medium": get_image_url_with_transformation(url, width=600, crop="limit", quality="auto"),
        "large": get_image_url_with_transformation(url, width=1200, crop="limit", quality="auto"),
        "original": url
    }