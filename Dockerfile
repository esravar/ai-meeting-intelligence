FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    git curl build-essential ffmpeg
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["bash"]