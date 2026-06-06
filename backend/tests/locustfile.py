"""
Load testing with Locust.

Install: pip install locust
Run:     locust -f locustfile.py --host=http://localhost:8000
Web UI:  http://localhost:8089
"""
import io
import struct

from locust import HttpUser, between, task


def _make_wav(duration_s=1.0, sr=22050) -> bytes:
    """Generate a minimal silent WAV in memory."""
    n = int(sr * duration_s)
    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + n * 2))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", n * 2))
    buf.write(b"\x00" * n * 2)
    return buf.getvalue()


WAV_BYTES = _make_wav()


class SERUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health(self):
        self.client.get("/api/v1/health")

    @task(3)
    def emotions(self):
        self.client.get("/api/v1/emotions")

    @task(2)
    def dashboard(self):
        self.client.get("/api/v1/dashboard")

    @task(5)
    def predict(self):
        self.client.post(
            "/api/v1/predict",
            files={"file": ("test.wav", WAV_BYTES, "audio/wav")},
        )

    @task(1)
    def model_info(self):
        self.client.get("/api/v1/model-info")
