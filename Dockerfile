FROM --platform=linux/amd64 python:3.10-slim


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir torch==2.1.2+cpu -f https://download.pytorch.org/whl/torch_stable.html


RUN pip install --no-cache-dir -r requirements.txt


COPY ./models/all-MiniLM-L6-v2 ./models/all-MiniLM-L6-v2


COPY . .


CMD ["python", "app.py"]
