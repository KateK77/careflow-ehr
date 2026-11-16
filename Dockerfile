FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=careflow.settings_hosted_demo
WORKDIR /app
COPY requirements.txt requirements-hosted.txt ./
RUN pip install --no-cache-dir -r requirements-hosted.txt && useradd --create-home appuser
COPY --chown=appuser:appuser manage.py ./
COPY --chown=appuser:appuser careflow ./careflow
COPY --chown=appuser:appuser deploy/container_start.py ./deploy/container_start.py
RUN mkdir /data /app/staticfiles && chown appuser:appuser /data /app/staticfiles
USER appuser
EXPOSE 8000
CMD ["python", "deploy/container_start.py"]
