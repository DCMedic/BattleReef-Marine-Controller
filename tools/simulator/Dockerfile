FROM python:3.12-slim

WORKDIR /app

COPY tools/simulator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY tools/simulator/publish_telemetry.py /app/publish_telemetry.py
COPY tools/simulator/device_command_listener.py /app/device_command_listener.py

CMD ["python", "/app/publish_telemetry.py"]