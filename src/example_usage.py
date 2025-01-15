import numpy as np
import time
import psutil
from data_generation import AudioDataGenerator
from data_conversion import WavConvertor
from audio_output import AudioOutput
from bluetooth_handler import BluetoothTransmitter
import logging
from queue import Queue
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='system.log')

# Function to log system resources
def log_system_resources():
    """Logs CPU, RAM usage, and uptime"""
    cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage in percentage
    ram_usage = psutil.virtual_memory().percent  # Get RAM usage in percentage
    uptime = time.time() - psutil.boot_time()  # Calculate system uptime in seconds
    
    logging.info(f"CPU Usage: {cpu_usage}%")
    logging.info(f"RAM Usage: {ram_usage}%")
    logging.info(f"System Uptime: {uptime//3600} hours {(uptime%3600)//60} minutes")

# Function to monitor for critical errors
def check_for_critical_errors():
    """Simulate checking for critical errors"""
    if psutil.virtual_memory().percent > 90:  # If RAM usage is above 90%
        logging.critical("Critical error: RAM usage exceeded 90%. Stopping services.")
        return True
    return False

def is_valid_mac(mac_address):
    if not isinstance(mac_address, str):
        try:
            mac_address = str(mac_address)
        except:
            return False
    
    # Remove any surrounding whitespace and quotes
    mac_address = mac_address.strip().strip('"').strip("'")
    
    # Different MAC address patterns
    patterns = [
        r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',  
        r'^([0-9A-Fa-f]{12})$' 
    ]
    
    return any(re.match(pattern, mac_address) for pattern in patterns)



def stream_with_output(duration_seconds=5, use_bluetooth=True, host="8C:64:A2:69:03:46"):
    """Stream audio through Bluetooth (if available) or speakers."""
    generator = AudioDataGenerator()
    audio_output = AudioOutput()
    
    if use_bluetooth:
        logging.info("Attempting to set up Bluetooth connection...")
        bluetooth_transmitter = BluetoothTransmitter(host=host)
        audio_output.setup_bluetooth(bluetooth_transmitter)
    
    logging.info("Starting audio generation and output...")
    generator.start()
    audio_output.start()
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            try:
                chunk = generator.get_chunk()
                if not audio_output.write(chunk):
                    logging.warning("Output buffer full")
            except Queue.Empty:
                logging.warning("Buffer underrun occurred")
                continue

            # Log system resources every 5 seconds
            if (time.time() - start_time) % 5 == 0:
                log_system_resources()
                
    finally:
        generator.stop()
        audio_output.stop()
        logging.info("Playback stopped")

def stream_with_fallback_demo(duration_seconds=5, host="8C:64:A2:69:03:46"):
    """Demonstrate Bluetooth streaming with automatic fallback to speakers."""
    print("Starting Bluetooth streaming demo with fallback...")
    print("First attempting Bluetooth connection...")
    
    stream_with_output(duration_seconds, use_bluetooth=True, host=host)

def full_demo():
    """Run a complete demonstration of all features."""
    print("=== Audio System Demo ===")
    
    
    
    print("\n. Streaming audio with Bluetooth/Speaker output...")
    host = input("give mac address of the bluetooth deviec: ")
    if not is_valid_mac(host):
        print("not a valid mac address defaulting to 8C:64:A2:69:03:46")
        host = "8C:64:A2:69:03:46"
    
    stream_with_fallback_demo(duration_seconds=5, host=host)
    
    logging.info("\n=== Demo Complete ===")

if __name__ == "__main__":
    try:
        full_demo()
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
