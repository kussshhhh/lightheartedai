import numpy as np
from queue import Queue
import threading 
import time 

class AudioDataGenerator:

    def __init__(self, sample_rate=44100, chunk_size=1024, buffer_size=10):
        
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.buffer = Queue(maxsize=buffer_size)
        self.is_running = False
        self.generator_thread = None

    def generate_chunk(self):
        return np.random.uniform(-1, 1, self.chunk_size)
    
    def generator_loop(self):
        while self.is_running:
            if not self.buffer.full():
                chunk = self.generate_chunk()
                try: 
                    self.buffer.put(chunk, timeout=1)
                except Queue.Full:
                    continue
            else:
                time.sleep(0.001)

    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.generator_thread = threading.Thread(target=self.generator_loop)
            self.generator_thread.daemon = True 
            self.generator_thread.start()

    def stop(self):
        self.is_running = False 
        if self.generator_thread:
            self.generator_thread.join()

    def get_chunk(self, timeout=1):
        return self.buffer.get(timeout=timeout)
    

if __name__=="__main__":
    generator = AudioDataGenerator()
    generator.start()

    try: 
        for _ in range(5):
            chunk = generator.get_chunk()
            print(f"Generator chunk with {len(chunk)} samples")
            print(f"Sample range: {chunk.min():.3f} to {chunk.max():.3f}")
            time.sleep(0.1)
    finally:
        generator.stop()