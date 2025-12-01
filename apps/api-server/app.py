#!/usr/bin/env python3
"""
Minimal REST API with observability hooks.
Demonstrates:
- Prometheus metrics collection
- Structured logging
- Health checks
- Graceful shutdown
"""
import os
import signal
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from threading import Thread

# Prometheus metrics
request_count = {}
request_duration = {}

# Structured logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        start_time = time.time()
        path = self.path
        
        # Health check endpoint
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'version': os.getenv('APP_VERSION', '1.0.0')
            }
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"Health check passed")
            return
        
        # Metrics endpoint for Prometheus
        if path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            metrics = self._generate_metrics()
            self.wfile.write(metrics.encode())
            return
        
        # Echo endpoint for testing
        if path.startswith('/api/echo'):
            duration = time.time() - start_time
            request_count[path] = request_count.get(path, 0) + 1
            request_duration[path] = duration
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                'message': 'pong',
                'hostname': os.getenv('HOSTNAME', 'unknown'),
                'timestamp': time.time()
            }
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"Request: {path} - Duration: {duration:.3f}s")
            return
        
        # 404
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'error': 'Not found'}
        self.wfile.write(json.dumps(response).encode())
    
    def _generate_metrics(self):
        """Generate Prometheus-format metrics"""
        metrics = [
            "# HELP api_requests_total Total number of requests",
            "# TYPE api_requests_total counter",
        ]
        for endpoint, count in request_count.items():
            metrics.append(f'api_requests_total{{endpoint="{endpoint}"}} {count}')
        
        metrics.append("# HELP api_request_duration_seconds Request duration")
        metrics.append("# TYPE api_request_duration_seconds gauge")
        for endpoint, duration in request_duration.items():
            metrics.append(f'api_request_duration_seconds{{endpoint="{endpoint}"}} {duration}')
        
        return "\n".join(metrics) + "\n"
    
    def log_message(self, format, *args):
        # Suppress default logging, we use structured logging
        pass

def main():
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    logger.info(f"Starting API server on port {port}")
    
    def handle_shutdown(signum, frame):
        logger.info("Shutdown signal received, gracefully stopping...")
        server.shutdown()
    
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logger.info("Server stopped")

if __name__ == '__main__':
    main()
