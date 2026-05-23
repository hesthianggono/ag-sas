FROM python:3.11-slim

WORKDIR /app

# Install system deps: gcc (compile), libpq-dev (psycopg2), fonts-liberation (PDF fallback)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    fonts-liberation \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Buat symlink font agar ReportLab bisa menemukan Arial-equivalent
# (Liberation Sans = metric-compatible dengan Arial)
RUN mkdir -p /usr/share/fonts/truetype/msttcorefonts && \
    ln -sf /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf \
           /usr/share/fonts/truetype/msttcorefonts/arial.ttf && \
    ln -sf /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf \
           /usr/share/fonts/truetype/msttcorefonts/arialbd.ttf && \
    ln -sf /usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf \
           /usr/share/fonts/truetype/msttcorefonts/ariali.ttf && \
    ln -sf /usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf \
           /usr/share/fonts/truetype/msttcorefonts/arialbi.ttf && \
    fc-cache -fv

EXPOSE 8000

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
