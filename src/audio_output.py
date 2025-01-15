# audio_output.py
import sounddevice as sd
import threading
import logging
from queue import Queue
import numpy as np
import time

class AudioOutput:
    def __init__(self, sample_rate=44100, channels=1, chunk_size=1024, buffer_size=20):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.buffer = Queue(maxsize=buffer_size)
        
        self.stream = None
        self.is_running = False
        self.playback_thread = None
        
        self.bluetooth = None
        self.use_bluetooth = False
    
    def setup_bluetooth(self, bluetooth_transmitter):
        self.bluetooth = bluetooth_transmitter
        if self.bluetooth.start_server():
            self.use_bluetooth = True
            logging.info("Bluetooth connection established")
        else:
            logging.warning("Falling back to speaker output")
            self.use_bluetooth = False
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            
            if not self.use_bluetooth:
                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    blocksize=self.chunk_size,
                    dtype=np.float32
                )
                self.stream.start()
            
            self.playback_thread = threading.Thread(target=self._playback_loop)
            self.playback_thread.daemon = True
            self.playback_thread.start()
    
    def _playback_loop(self):
        while self.is_running:
            try:
                data = self.buffer.get(timeout=1)
                
                if self.use_bluetooth and self.bluetooth:
                    # Convert float32 to bytes for Bluetooth transmission
                    data_bytes = (data * 32767).astype(np.int16).tobytes()
                    if not self.bluetooth.send_data(data_bytes):
                        logging.warning("Bluetooth transmission failed, falling back to speaker")
                        self.use_bluetooth = False
                        self._setup_audio_stream()
                
                if not self.use_bluetooth and self.stream:
                    self.stream.write(data.astype(np.float32))
                    
            except Queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Playback error: {str(e)}")
                break
    
    def _setup_audio_stream(self):
        if not self.stream:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.chunk_size,
                dtype=np.float32
            )
            self.stream.start()
    
    def write(self, data):
        try:
            self.buffer.put(data, timeout=1)
            return True
        except Queue.Full:
            logging.warning("Audio output buffer full")
            return False
    
    def stop(self):
        self.is_running = False
        
        if self.playback_thread:
            self.playback_thread.join()
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if self.bluetooth:
            self.bluetooth.cleanup()