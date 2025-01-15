import numpy as np 
import wave 
from typing import List, Union

class WavConvertor:
    def __init__(self, sample_rate: int = 44100, channels: int = 1, sample_width: int = 2):
        self.sample_rate=sample_rate
        self.channels=channels
        self.sample_width = sample_width

    def numpy_to_wav_bytes(self, audio_data: Union[np.ndarray, List[np.ndarray]]) -> bytes:
        if isinstance(audio_data, np.ndarray):
            audio_data = [audio_data]
        
        if len(audio_data) != self.channels:
            raise ValueError(f"Expected {self.channels} channels, got {len(audio_data)}")
        
        max_int16 = 32767
        audio_data_int = [np.int16(data * max_int16) for data in audio_data]

        if self.channels == 2:
            audio_data_int = np.vstack(audio_data_int[0], audio_data_int[1]).T.flatten()
        else:
            audio_data_int = audio_data_int[0]

        byte_data = audio_data_int.tobytes()

        import io
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(byte_data)

        return wav_buffer.getvalue()
    

    def save_to_wav(self, audio_data: Union[np.ndarray, List[np.ndarray]], filename: str):
        with open(filename, 'wb') as f:
            f.write(self.numpy_to_wav_bytes(audio_data))
            
    def convert_chunk_stream(self, chunk_iterator, output_filename: str):
        with wave.open(output_filename, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.sample_rate)
            
            for chunk in chunk_iterator:
                # Convert float32 (-1 to 1) to int16 (-32768 to 32767)
                chunk_int = np.int16(chunk * 32767)
                wav_file.writeframes(chunk_int.tobytes())
 