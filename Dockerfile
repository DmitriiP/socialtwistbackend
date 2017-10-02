FROM python:3
RUN apt-get update && apt-get install -y libgdal-dev
# Copy reqs separatly so that the build cache doesn't invalidate
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
WORKDIR /app
COPY . /app
RUN ./manage.py collectstatic --noinput
EXPOSE 49472
ENV HOST_NAME='social-twist.com'
CMD uwsgi uwsgi.ini
