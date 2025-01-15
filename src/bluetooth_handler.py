import socket
import threading
import logging
from queue import Queue
import time

class BluetoothTransmitter:
    def __init__(self, host='0.0.0.0', port=5000, buffer_size=20):
        
        self.host = host
        self.port = port
        self.server_sock = None
        self.client_sock = None
        self.is_connected = False
        self.buffer = Queue(maxsize=buffer_size)
        self.transmit_thread = None
        self.is_running = False
        
    def start_server(self):
        """Start the TCP server and wait for a client connection."""
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind((self.host, self.port))
            self.server_sock.listen(1)
            
            logging.info(f"Waiting for connection on {self.host}:{self.port}")
            
            self.client_sock, client_info = self.server_sock.accept()
            self.is_connected = True
            logging.info(f"Accepted connection from {client_info}")
            
            self.is_running = True
            self.transmit_thread = threading.Thread(target=self._transmit_loop)
            self.transmit_thread.daemon = True
            self.transmit_thread.start()
            
            return True
        except Exception as e:
            logging.error(f"Server error: {str(e)}")
            self.cleanup()
            return False
    
    def _transmit_loop(self):
        """Main transmission loop that sends data to the connected client."""
        while self.is_running and self.is_connected:
            try:
                data = self.buffer.get(timeout=1)
                # First send the size of the data
                size = len(data)
                self.client_sock.send(size.to_bytes(4, byteorder='big'))
                # Then send the actual data
                total_sent = 0
                while total_sent < size:
                    sent = self.client_sock.send(data[total_sent:])
                    if sent == 0:
                        raise RuntimeError("Socket connection broken")
                    total_sent += sent
            except Queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Transmission error: {str(e)}")
                self.cleanup()
                break
    
    def send_data(self, data):
        """
        Queue data for transmission to the client.
        
        Args:
            data (bytes): The audio data to send
            
        Returns:
            bool: True if data was queued successfully, False otherwise
        """
        if self.is_connected:
            try:
                self.buffer.put(data, timeout=1)
                return True
            except Queue.Full:
                logging.warning("Transmission buffer full")
                return False
        return False
    
    def cleanup(self):
        """Clean up all resources and close connections."""
        self.is_running = False
        self.is_connected = False
        
        if self.transmit_thread:
            self.transmit_thread.join()
        
        if self.client_sock:
            try:
                self.client_sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.client_sock.close()
        
        if self.server_sock:
            try:
                self.server_sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.server_sock.close()