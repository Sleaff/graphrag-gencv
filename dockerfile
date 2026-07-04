FROM python:3.13-slim

# Install Tectonic
RUN apt-get update && apt-get install -y \
    curl \
    && curl -LO https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz \
    && tar -xzf tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz \
    && mv tectonic /usr/local/bin/ \
    && rm tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz

# Rest todo here...



# 

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]