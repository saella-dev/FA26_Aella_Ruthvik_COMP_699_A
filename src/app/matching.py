
"""
Explainable baseline image comparison.

This module compares manuscript fragment images using grayscale
preprocessing, edge detection, and cosine similarity.

This is a preliminary image-matching baseline.
It is not a trained restoration model and does not verify
historical relationships between manuscript fragments.
"""

import math
import os

from PIL import (
    Image,
    ImageFilter,
    ImageOps,
    UnidentifiedImageError,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DESCRIPTOR_SIZE = 48
MAX_IMAGE_SIZE = 512


# ---------------------------------------------------------
# Image descriptor
# ---------------------------------------------------------

def image_descriptor(path, size=DESCRIPTOR_SIZE):
    """
    Convert a manuscript image into a normalized edge descriptor.

    Processing steps:
        1. Validate the image path.
        2. Open and convert the image to grayscale.
        3. Correct image orientation.
        4. Resize the image.
        5. Detect edges.
        6. Normalize pixel intensity values.

    Returns:
        A list of normalized edge-intensity values.
    """

    if not path:
        raise ValueError("Image path is empty.")

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Image file not found: {path}"
        )

    if size <= 0:
        raise ValueError(
            "Descriptor size must be greater than zero."
        )

    try:
        with Image.open(path) as original:

            # Correct orientation using EXIF information.
            image = ImageOps.exif_transpose(original)

            # Convert the image to grayscale.
            image = image.convert("L")

            # Reduce large images before descriptor generation.
            image.thumbnail(
                (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE)
            )

            # Resize and crop to a consistent descriptor size.
            image = ImageOps.fit(
                image,
                (size, size)
            )

            # Detect image edges.
            edges = image.filter(
                ImageFilter.FIND_EDGES
            )

            pixels = list(edges.getdata())

    except (UnidentifiedImageError, OSError) as error:
        raise ValueError(
            f"Unable to process image: {path}"
        ) from error

    if not pixels:
        raise ValueError(
            "Image descriptor contains no pixel data."
        )

    # Calculate mean edge intensity.
    mean_intensity = sum(pixels) / len(pixels)

    # Normalize intensity values around their mean.
    normalized = [
        (pixel - mean_intensity) / 255.0
        for pixel in pixels
    ]

    return normalized


# ---------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------

def cosine_similarity(descriptor_a, descriptor_b):
    """
    Calculate cosine similarity between two image descriptors.

    Returns:
        A similarity value between 0 and 100.
    """

    if len(descriptor_a) != len(descriptor_b):
        raise ValueError(
            "Image descriptors must have equal lengths."
        )

    if not descriptor_a:
        return 0.0

    dot_product = sum(
        a * b
        for a, b in zip(descriptor_a, descriptor_b)
    )

    norm_a = math.sqrt(
        sum(value * value for value in descriptor_a)
    )

    norm_b = math.sqrt(
        sum(value * value for value in descriptor_b)
    )

    # Avoid division by zero for blank or uniform images.
    if norm_a == 0 or norm_b == 0:
        return 0.0

    cosine = dot_product / (norm_a * norm_b)

    # Keep floating-point rounding within valid bounds.
    cosine = max(
        -1.0,
        min(1.0, cosine)
    )

    # Convert cosine similarity from [-1, 1] to [0, 100].
    score = (cosine + 1.0) * 50.0

    return round(score, 2)


# ---------------------------------------------------------
# Manuscript image comparison
# ---------------------------------------------------------

def similarity(path_a, path_b):
    """
    Compare two manuscript fragment images.

    Returns:
        A score between 0 and 100.

    Higher scores indicate greater similarity between the
    normalized grayscale edge descriptors.

    The score is a preliminary visual similarity measure,
    not a probability or historical verification result.
    """

    descriptor_a = image_descriptor(path_a)
    descriptor_b = image_descriptor(path_b)

    return cosine_similarity(
        descriptor_a,
        descriptor_b
    )

