"""
Image processing utilities for product images.
Enforces 1:1 ratio, 800x800 size, and WebP format.
"""
from PIL import Image
import io
from typing import Tuple, Optional


def process_product_image(
    image_bytes: bytes,
    target_size: Tuple[int, int] = (800, 800),
    format_preference: str = "WEBP"
) -> bytes:
    """
    Process product image to enforce requirements:
    - 1:1 aspect ratio (square)
    - Target size (default: 800x800)
    - WebP format (with JPEG fallback)
    
    Args:
        image_bytes: Raw image bytes from upload
        target_size: Target dimensions as (width, height) tuple. Default: (800, 800)
        format_preference: Preferred format. Default: "WEBP"
    
    Returns:
        Processed image bytes in WebP format (or JPEG if WebP fails)
    
    Raises:
        ValueError: If image cannot be opened or processed
        IOError: If image format is not supported
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if image.mode != "RGB":
            # Create a white background for transparency
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "RGBA":
                rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Get current dimensions
        width, height = image.size
        
        # Calculate the size for 1:1 ratio (use the larger dimension)
        size_for_square = max(width, height)
        
        # Create a square image with white background
        square_image = Image.new("RGB", (size_for_square, size_for_square), (255, 255, 255))
        
        # Calculate position to center the original image
        paste_x = (size_for_square - width) // 2
        paste_y = (size_for_square - height) // 2
        
        # Paste the original image centered on the square canvas
        square_image.paste(image, (paste_x, paste_y))
        
        # Resize to target size (maintains 1:1 ratio)
        resized_image = square_image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to bytes in preferred format
        output = io.BytesIO()
        
        try:
            # Try WebP first
            if format_preference.upper() == "WEBP":
                resized_image.save(output, format="WEBP", quality=85, method=6)
                output.seek(0)
                return output.getvalue()
        except Exception:
            # Fallback to JPEG if WebP fails
            pass
        
        # JPEG fallback
        output = io.BytesIO()
        resized_image.save(output, format="JPEG", quality=85, optimize=True)
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def validate_image_file(image_bytes: bytes, max_size_mb: float = 10.0) -> bool:
    """
    Validate image file before processing.
    
    Args:
        image_bytes: Image bytes to validate
        max_size_mb: Maximum file size in MB. Default: 10.0
    
    Returns:
        True if valid, False otherwise
    
    Raises:
        ValueError: If image is invalid or too large
    """
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(image_bytes) > max_size_bytes:
        raise ValueError(f"Image file too large. Maximum size: {max_size_mb}MB")
    
    # Try to open and verify it's a valid image
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verify it's a valid image file
        return True
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")


def get_image_info(image_bytes: bytes) -> dict:
    """
    Get basic information about an image.
    
    Args:
        image_bytes: Image bytes
    
    Returns:
        Dictionary with image information (format, size, mode)
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return {
            "format": image.format,
            "size": image.size,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
        }
    except Exception as e:
        raise ValueError(f"Failed to read image info: {str(e)}")

