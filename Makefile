.PHONY: up backend frontend install-backend install-frontend clean

# Run the entire application (backend and frontend in background)
up:
	@echo "Starting backend and frontend servers..."
	uvicorn src.main:app --reload --port 8000 &
	cd frontend && npm run dev &

# Run the backend server
backend:
	@echo "Starting backend server..."
	uvicorn src.main:app --reload --port 8000

# Run the frontend development server
frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

# Install backend dependencies
install-backend:
	@echo "Installing backend dependencies..."
	pip install -r requirements.txt

# Install frontend dependencies
install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Install all dependencies
install: install-backend install-frontend

# Clean up (stop processes, etc.)
clean:
	@echo "Cleaning up..."
	-pkill -f uvicorn
	-pkill -f "npm run dev"