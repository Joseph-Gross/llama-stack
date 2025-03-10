# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field

from llama_stack.apis.common.content_types import URL, InterleavedContent
from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class ImageFormat(Enum):
    """Supported image formats.
    
    :cvar PNG: PNG image format
    :cvar JPEG: JPEG image format
    :cvar WEBP: WebP image format
    :cvar GIF: GIF image format
    """
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"


class AudioFormat(Enum):
    """Supported audio formats.
    
    :cvar MP3: MP3 audio format
    :cvar WAV: WAV audio format
    :cvar OGG: OGG audio format
    :cvar FLAC: FLAC audio format
    """
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"


class DocumentFormat(Enum):
    """Supported document formats.
    
    :cvar PDF: PDF document format
    :cvar DOCX: Microsoft Word document format
    :cvar TXT: Plain text document format
    :cvar HTML: HTML document format
    :cvar MARKDOWN: Markdown document format
    """
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    MARKDOWN = "markdown"


@json_schema_type
class ImageGenerationParams(BaseModel):
    """Parameters for image generation.
    
    :param prompt: Text prompt for image generation
    :param negative_prompt: Text prompt for elements to avoid in the image
    :param width: Width of the generated image
    :param height: Height of the generated image
    :param num_images: Number of images to generate
    :param seed: Random seed for reproducibility
    :param format: Format of the generated image
    :param style: Style of the generated image
    :param additional_params: Additional parameters for the image generation model
    """
    prompt: str
    negative_prompt: Optional[str] = None
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    num_images: Optional[int] = 1
    seed: Optional[int] = None
    format: Optional[ImageFormat] = ImageFormat.PNG
    style: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class ImageEditParams(BaseModel):
    """Parameters for image editing.
    
    :param image_url: URL of the image to edit
    :param mask_url: URL of the mask image (optional)
    :param prompt: Text prompt for the edit
    :param negative_prompt: Text prompt for elements to avoid
    :param width: Width of the output image
    :param height: Height of the output image
    :param format: Format of the output image
    :param additional_params: Additional parameters for the image editing model
    """
    image_url: URL
    mask_url: Optional[URL] = None
    prompt: str
    negative_prompt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[ImageFormat] = ImageFormat.PNG
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class ImageVariationParams(BaseModel):
    """Parameters for generating image variations.
    
    :param image_url: URL of the image to create variations of
    :param num_variations: Number of variations to generate
    :param variation_strength: Strength of the variation (0.0 to 1.0)
    :param width: Width of the output images
    :param height: Height of the output images
    :param seed: Random seed for reproducibility
    :param format: Format of the output images
    :param additional_params: Additional parameters for the variation model
    """
    image_url: URL
    num_variations: Optional[int] = 1
    variation_strength: Optional[float] = 0.75
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    format: Optional[ImageFormat] = ImageFormat.PNG
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class ImageAnalysisParams(BaseModel):
    """Parameters for image analysis.
    
    :param image_url: URL of the image to analyze
    :param analysis_type: Type of analysis to perform
    :param detect_objects: Whether to detect objects in the image
    :param detect_text: Whether to detect text in the image
    :param detect_faces: Whether to detect faces in the image
    :param detect_labels: Whether to detect labels/categories in the image
    :param additional_params: Additional parameters for the analysis model
    """
    image_url: URL
    analysis_type: Optional[str] = "general"
    detect_objects: Optional[bool] = False
    detect_text: Optional[bool] = False
    detect_faces: Optional[bool] = False
    detect_labels: Optional[bool] = True
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class SpeechToTextParams(BaseModel):
    """Parameters for speech-to-text conversion.
    
    :param audio_url: URL of the audio file
    :param language: Language code (e.g., "en-US")
    :param model: Model to use for transcription
    :param prompt: Optional prompt to guide transcription
    :param additional_params: Additional parameters for the transcription model
    """
    audio_url: URL
    language: Optional[str] = "en-US"
    model: Optional[str] = None
    prompt: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class TextToSpeechParams(BaseModel):
    """Parameters for text-to-speech conversion.
    
    :param text: Text to convert to speech
    :param voice: Voice to use for synthesis
    :param language: Language code (e.g., "en-US")
    :param speed: Speech speed (0.5 to 2.0)
    :param format: Format of the output audio
    :param additional_params: Additional parameters for the synthesis model
    """
    text: str
    voice: Optional[str] = "default"
    language: Optional[str] = "en-US"
    speed: Optional[float] = 1.0
    format: Optional[AudioFormat] = AudioFormat.MP3
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class DocumentAnalysisParams(BaseModel):
    """Parameters for document analysis.
    
    :param document_url: URL of the document to analyze
    :param analysis_type: Type of analysis to perform
    :param extract_text: Whether to extract text from the document
    :param extract_tables: Whether to extract tables from the document
    :param extract_forms: Whether to extract forms from the document
    :param extract_images: Whether to extract images from the document
    :param additional_params: Additional parameters for the analysis model
    """
    document_url: URL
    analysis_type: Optional[str] = "general"
    extract_text: Optional[bool] = True
    extract_tables: Optional[bool] = False
    extract_forms: Optional[bool] = False
    extract_images: Optional[bool] = False
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class GeneratedImage(BaseModel):
    """Generated image result.
    
    :param image_url: URL of the generated image
    :param prompt: Prompt used to generate the image
    :param seed: Seed used for generation
    :param width: Width of the generated image
    :param height: Height of the generated image
    :param format: Format of the generated image
    :param metadata: Additional metadata about the generation
    """
    image_url: URL
    prompt: str
    seed: Optional[int] = None
    width: int
    height: int
    format: ImageFormat
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class ImageGenerationResponse(BaseModel):
    """Response from image generation.
    
    :param images: List of generated images
    """
    images: List[GeneratedImage]


@json_schema_type
class ImageAnalysisResult(BaseModel):
    """Result of image analysis.
    
    :param image_url: URL of the analyzed image
    :param caption: Generated caption for the image
    :param objects: Detected objects in the image
    :param text: Detected text in the image
    :param faces: Detected faces in the image
    :param labels: Detected labels/categories in the image
    :param metadata: Additional metadata about the analysis
    """
    image_url: URL
    caption: Optional[str] = None
    objects: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    text: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    faces: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    labels: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class SpeechToTextResult(BaseModel):
    """Result of speech-to-text conversion.
    
    :param audio_url: URL of the original audio
    :param text: Transcribed text
    :param language: Detected or specified language
    :param segments: Time-aligned segments of the transcription
    :param metadata: Additional metadata about the transcription
    """
    audio_url: URL
    text: str
    language: str
    segments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class TextToSpeechResult(BaseModel):
    """Result of text-to-speech conversion.
    
    :param text: Original text
    :param audio_url: URL of the generated audio
    :param voice: Voice used for synthesis
    :param language: Language used for synthesis
    :param duration: Duration of the audio in seconds
    :param format: Format of the generated audio
    :param metadata: Additional metadata about the synthesis
    """
    text: str
    audio_url: URL
    voice: str
    language: str
    duration: float
    format: AudioFormat
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class DocumentAnalysisResult(BaseModel):
    """Result of document analysis.
    
    :param document_url: URL of the analyzed document
    :param text: Extracted text from the document
    :param tables: Extracted tables from the document
    :param forms: Extracted forms from the document
    :param images: Extracted images from the document
    :param metadata: Additional metadata about the analysis
    """
    document_url: URL
    text: Optional[str] = None
    tables: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    forms: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    images: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@runtime_checkable
@trace_protocol
class Multimodal(Protocol):
    """Llama Stack Multimodal API for working with images, audio, and documents.
    
    This API provides enterprise-grade multimodal capabilities for Llama Stack:
    - Image generation, editing, and analysis
    - Speech-to-text and text-to-speech conversion
    - Document understanding and analysis
    - Multimodal content processing
    """
    
    @webmethod(route="/multimodal/images/generate", method="POST")
    async def generate_image(
        self,
        params: ImageGenerationParams,
    ) -> ImageGenerationResponse:
        """Generate images from a text prompt.
        
        :param params: Parameters for image generation
        :returns: Generated images
        """
        ...
    
    @webmethod(route="/multimodal/images/edit", method="POST")
    async def edit_image(
        self,
        params: ImageEditParams,
    ) -> ImageGenerationResponse:
        """Edit an existing image based on a text prompt.
        
        :param params: Parameters for image editing
        :returns: Edited images
        """
        ...
    
    @webmethod(route="/multimodal/images/variations", method="POST")
    async def create_image_variations(
        self,
        params: ImageVariationParams,
    ) -> ImageGenerationResponse:
        """Create variations of an existing image.
        
        :param params: Parameters for creating image variations
        :returns: Generated image variations
        """
        ...
    
    @webmethod(route="/multimodal/images/analyze", method="POST")
    async def analyze_image(
        self,
        params: ImageAnalysisParams,
    ) -> ImageAnalysisResult:
        """Analyze an image to extract information.
        
        :param params: Parameters for image analysis
        :returns: Analysis results
        """
        ...
    
    @webmethod(route="/multimodal/speech/transcribe", method="POST")
    async def speech_to_text(
        self,
        params: SpeechToTextParams,
    ) -> SpeechToTextResult:
        """Convert speech to text.
        
        :param params: Parameters for speech-to-text conversion
        :returns: Transcription results
        """
        ...
    
    @webmethod(route="/multimodal/speech/synthesize", method="POST")
    async def text_to_speech(
        self,
        params: TextToSpeechParams,
    ) -> TextToSpeechResult:
        """Convert text to speech.
        
        :param params: Parameters for text-to-speech conversion
        :returns: Synthesis results
        """
        ...
    
    @webmethod(route="/multimodal/documents/analyze", method="POST")
    async def analyze_document(
        self,
        params: DocumentAnalysisParams,
    ) -> DocumentAnalysisResult:
        """Analyze a document to extract information.
        
        :param params: Parameters for document analysis
        :returns: Analysis results
        """
        ...
