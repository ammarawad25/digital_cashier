#!/bin/bash

# Build the frontend
cd frontend
npm install
npm run build
cd ..

# Copy built files to src/static for serving
mkdir -p src/static
cp -r frontend/dist/* src/static/