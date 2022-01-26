FROM python:3.10-alpine
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
RUN adduser -D webapp
RUN chown webapp:webapp /code

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
EXPOSE 8000

USER webapp
COPY --chown=webapp:webapp app.py /code/

CMD ["gunicorn", "--workers", "5", "-b", "0.0.0.0:8000", "--error-logfile", "-", "--access-logfile", "-", "app"]
