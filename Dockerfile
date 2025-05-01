# Stage 1: Build stage for installing dependencies and building the app
FROM python:3.12.2-alpine3.19 as builder

# Set the working directory in the container
WORKDIR /app

# Install build dependencies, fonts, and FontConfig
RUN apk add --no-cache --virtual .build-deps \
        build-base \
        python3-dev \
        libpq \
        geos-dev \
        file \
        cairo-dev \
        pango-dev \
        gdk-pixbuf-dev \
        gobject-introspection-dev \
        libffi-dev \
    && apk add --no-cache \
        ttf-freefont \
        ttf-dejavu \
        fontconfig \
    && pip install --no-cache-dir poetry

# Copy only pyproject.toml and poetry.lock* (if they exist) to cache dependencies
COPY pyproject.toml poetry.lock* /app/

# Disable virtual env creation by Poetry as Docker container acts as an isolated environment
RUN poetry config virtualenvs.create false

# Install project dependencies, including dev dependencies for building
RUN poetry install --no-root --no-interaction --no-ansi

# Stage 2: Runtime stage to create the final runtime image
FROM python:3.12.2-alpine3.19

# Set the working directory in the container
WORKDIR /app

# Install runtime dependencies and fonts
RUN apk add --no-cache \
        libpq \
        file \
        geos \
        cairo \
        pango \
        gdk-pixbuf \
        gobject-introspection \
        libffi \
        ttf-freefont \
        ttf-dejavu \
        fontconfig

# Copy the installed Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the current directory contents into the container at /app
COPY . /app

# Expose the port the application runs on
EXPOSE 8000

# Start the application using Poetry
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
