# URL HTML Hash

A Tower app that fetches HTML content from a URL, calculates a SHA-256 hash, and stores both in an Iceberg table.

## Overview

This app:
1. Fetches HTML content from a specified URL
2. Calculates a SHA-256 hash of the content
3. Stores the URL, HTML content, hash, timestamp, and content length in a Tower Iceberg table

## App Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `URL` | The URL to fetch HTML content from | `https://example.com` |

## Prerequisites

- Tower CLI installed and configured
- An Iceberg catalog named `default` configured in Tower

## Setup

### 1. Install Dependencies

```bash
cd 20-url-html-hash
uv sync
```

### 2. Configure Iceberg Catalog

Check if a `default` catalog exists:

```bash
tower catalogs list
```

If not, create one:

```bash
tower catalogs create default
```

### 3. Run Locally

```bash
tower run --local
```

Or with a custom URL:

```bash
tower run --local --param URL=https://news.ycombinator.com
```

## Deploying to Tower

### Deploy the App

```bash
tower deploy
```

### Run on Tower Cloud

```bash
tower run
```

Or with a custom URL:

```bash
tower run --param URL=https://github.com
```

## Monitoring

### Check App Status

```bash
tower apps show url-html-hash
```

### View Run Logs

```bash
tower apps logs "url-html-hash#1"
```

## Table Schema

The app creates/uses a table named `url_html_snapshots` with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `url` | string | The source URL |
| `html_content` | large_string | The fetched HTML content |
| `content_hash` | string | SHA-256 hash of the HTML content |
| `fetched_at` | string | ISO timestamp of when content was fetched |
| `content_length` | int64 | Length of the HTML content in characters |

## Use Cases

- **Content Change Detection**: Track when web pages change by comparing hashes
- **Web Archiving**: Store snapshots of web pages over time
- **Data Pipeline Input**: Use as a source for downstream processing pipelines
