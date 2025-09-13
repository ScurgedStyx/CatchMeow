import os
from mistralai import Mistral
## Testing
class AudioTranscriber:
    """
    A class to handle MP3 audio transcription using Mistral's Voxtral model.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the AudioTranscriber with Mistral API key.
        
        Args:
            api_key (str): Mistral API key. If None, will try to get from environment.
        """
        if api_key is None:
            api_key = os.environ.get("MISTRAL_API_KEY", 'ddi3VI49KfMT0clWpxLImBwGDBOgB9tj')
        
        if api_key is None:
            api_key = os.environ.get("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("MISTRAL_API_KEY not found in environment variables")
        
        self.api_key = api_key
        self.model = "voxtral-mini-latest"
        self.client = Mistral(api_key=api_key)
    
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe an MP3 audio file to text.
        
        Args:
            audio_file_path (str): Path to the MP3 audio file
        
        Returns:
            str: Transcribed text from the audio
        
        Raises:
            FileNotFoundError: If the audio file doesn't exist
            Exception: If transcription fails
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        try:
            # Upload the audio file
            with open(audio_file_path, "rb") as f:
                uploaded_audio = self.client.files.upload(
                    file={
                        "content": f,
                        "file_name": os.path.basename(audio_file_path),
                    },
                    purpose="audio"
                )
            
            # Get the signed URL
            signed_url = self.client.files.get_signed_url(file_id=uploaded_audio.id)
            
            # Get the transcription
            transcription_params = {
                "model": self.model,
                "file_url": signed_url.url,
                "language": "en"
            }
            
            transcription_response = self.client.audio.transcriptions.complete(**transcription_params)
            
            return transcription_response.text if hasattr(transcription_response, 'text') else str(transcription_response)
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_from_bytes(self, audio_bytes, filename="audio.mp3"):
        """
        Transcribe audio from bytes data.
        
        Args:
            audio_bytes (bytes): Audio file content as bytes
            filename (str): Filename to use for upload
        
        Returns:
            str: Transcribed text from the audio
        """
        try:
            # Upload the audio bytes
            uploaded_audio = self.client.files.upload(
                file={
                    "content": audio_bytes,
                    "file_name": filename,
                },
                purpose="audio"
            )
            
            # Get the signed URL
            signed_url = self.client.files.get_signed_url(file_id=uploaded_audio.id)
            
            # Get the transcription
            transcription_params = {
                "model": self.model,
                "file_url": signed_url.url,
                "language": "en"
            }
            
            transcription_response = self.client.audio.transcriptions.complete(**transcription_params)
            
            return transcription_response.text if hasattr(transcription_response, 'text') else str(transcription_response)
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")