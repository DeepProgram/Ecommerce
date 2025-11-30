"""
Image processing utilities for product images.
Generates multiple sizes with smart cropping (no white padding).
"""
from PIL import Image
import io
from typing import Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class ProcessedImage:
    """Container for processed image data"""
    bytes: bytes
    width: int
    height: int
    format: str


def process_product_image(
    image_bytes: bytes,
    max_dimension: int = 1200,
    format_preference: str = "WEBP",
    preserve_aspect_ratio: bool = True
) -> ProcessedImage:
    """
    Process product image preserving aspect ratio (no cropping, no white padding).
    - Preserves original aspect ratio (portrait stays portrait, landscape stays landscape)
    - Resizes to fit within max_dimension (longest side)
    - WebP format (with JPEG fallback)
    
    Args:
        image_bytes: Raw image bytes from upload
        max_dimension: Maximum dimension (width or height). Default: 1200px
        format_preference: Preferred format. Default: "WEBP"
        preserve_aspect_ratio: If True, preserves aspect ratio. Default: True
    
    Returns:
        ProcessedImage object with bytes, dimensions, and format
    
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
        
        # Calculate new dimensions preserving aspect ratio
        if preserve_aspect_ratio:
            # Resize to fit within max_dimension while preserving aspect ratio
            if width > height:
                # Landscape or square: fit to width
                if width > max_dimension:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_width = width
                    new_height = height
            else:
                # Portrait: fit to height
                if height > max_dimension:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                else:
                    new_width = width
                    new_height = height
        else:
            # Don't preserve (shouldn't happen, but fallback)
            new_width = min(width, max_dimension)
            new_height = min(height, max_dimension)
        
        # Resize image (maintains aspect ratio, no distortion, no cropping)
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to bytes in preferred format
        output = io.BytesIO()
        image_format = "JPEG"
        
        try:
            # Try WebP first
            if format_preference.upper() == "WEBP":
                resized_image.save(output, format="WEBP", quality=85, method=6)
                image_format = "WEBP"
                output.seek(0)
                return ProcessedImage(
                    bytes=output.getvalue(),
                    width=new_width,
                    height=new_height,
                    format=image_format
                )
        except Exception:
            # Fallback to JPEG if WebP fails
            pass
        
        # JPEG fallback
        output = io.BytesIO()
        resized_image.save(output, format="JPEG", quality=85, optimize=True)
        output.seek(0)
        return ProcessedImage(
            bytes=output.getvalue(),
            width=new_width,
            height=new_height,
            format="JPEG"
        )
        
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def process_product_image_multiple_sizes(
    image_bytes: bytes,
    format_preference: str = "WEBP"
) -> Dict[str, ProcessedImage]:
    """
    Process product image and generate multiple sizes (thumbnail, medium, large).
    Preserves aspect ratio for all sizes. Follows e-commerce best practices.
    
    Args:
        image_bytes: Raw image bytes from upload
        format_preference: Preferred format. Default: "WEBP"
    
    Returns:
        Dictionary with keys: 'thumbnail', 'medium', 'large'
        Each value is a ProcessedImage object with preserved aspect ratio
    """
    max_dimensions = {
        "thumbnail": 200,
        "medium": 600,
        "large": 1200
    }
    
    results = {}
    for size_name, max_dim in max_dimensions.items():
        results[size_name] = process_product_image(
            image_bytes,
            max_dimension=max_dim,
            format_preference=format_preference,
            preserve_aspect_ratio=True
        )
    
    return results


def process_single_size(
    image_bytes: bytes,
    max_dimension: int = 1200,
    format_preference: str = "WEBP"
) -> ProcessedImage:
    """
    Process image to a single size (convenience function).
    Preserves aspect ratio.
    
    Args:
        image_bytes: Raw image bytes from upload
        max_dimension: Maximum dimension (width or height). Default: 1200px
        format_preference: Preferred format. Default: "WEBP"
    
    Returns:
        ProcessedImage object
    """
    return process_product_image(
        image_bytes,
        max_dimension=max_dimension,
        format_preference=format_preference,
        preserve_aspect_ratio=True
    )


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

