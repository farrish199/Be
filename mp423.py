from moviepy.editor import VideoFileClip
import io

def mp4_to_audio(mp4_stream: io.BytesIO) -> io.BytesIO:
    """Convert MP4 video stream to audio and return the audio in a BytesIO stream."""
    # Load the MP4 video file from the stream
    video = VideoFileClip(mp4_stream)
    
    # Extract audio from the video
    audio = video.audio
    
    # Save the audio to a BytesIO stream
    audio_stream = io.BytesIO()
    audio.write_audiofile(audio_stream, format='mp3')  # Save as MP3 format
    audio_stream.seek(0)
    
    return audio_stream
