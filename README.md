
# LA County Hospital Vacancy & Navigation System

A full-stack hospital navigation prototype that helps users explore hospitals in Los Angeles County through an interactive map.

## Features

- Interactive map showing 30 LA County hospitals
- Search hospitals by name or city
- Filter hospitals by availability and specialty
- View simulated ER, ICU, and general bed availability
- View estimated waiting times
- Explore hospital locations using OpenStreetMap

## Technologies

- Python and FastAPI — Backend
- SQLite — Database
- HTML, CSS, and JavaScript — Frontend
- Leaflet.js and OpenStreetMap — Interactive mapping

## How to Run

1. Install the Python dependencies, including FastAPI, Uvicorn, SQLAlchemy, python-multipart, and compatible authentication packages.
2. Start the backend from the project directory:

   `python3 -m uvicorn main:app --reload --port 8000`

3. Open `index.html` in your browser.

## Development Status

This is a demonstration project, not a production healthcare application.

Hospital locations are based on real facilities, but bed availability and estimated wait times are simulated. They are not real-time hospital data.

The AI recommendation feature is under development and is not currently functional.

This application should not be used to make medical or emergency-care decisions.

## Project Purpose

This project demonstrates full-stack development, database integration, API development, interactive mapping, and software prototyping.
