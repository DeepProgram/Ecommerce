#!/bin/bash

case "$1" in
  start)
    echo "Starting all services..."
    docker-compose up -d
    ;;
  start-with-workers)
    echo "Starting all services with workers..."
    docker-compose -f docker-compose.yml -f docker-compose.workers.yml up -d
    ;;
  stop)
    echo "Stopping all services..."
    docker-compose down
    ;;
  restart)
    echo "Restarting all services..."
    docker-compose restart
    ;;
  logs)
    docker-compose logs -f ${2:-backend}
    ;;
  migrate)
    echo "Running migrations..."
    docker-compose exec backend python manage.py migrate
    ;;
  makemigrations)
    echo "Creating migrations..."
    docker-compose exec backend python manage.py makemigrations
    ;;
  createsuperuser)
    echo "Creating superuser..."
    docker-compose exec backend python manage.py createsuperuser
    ;;
  shell)
    echo "Opening Django shell..."
    docker-compose exec backend python manage.py shell
    ;;
  init-search)
    echo "Initializing Elasticsearch index..."
    docker-compose exec backend python manage.py init_search
    ;;
  seed-products)
    echo "Seeding database with demo products..."
    docker-compose exec backend python manage.py seed_products
    ;;
  test)
    echo "Running tests..."
    docker-compose exec backend python manage.py test
    ;;
  clean)
    echo "Cleaning up containers and volumes..."
    docker-compose down -v
    ;;
  rebuild)
    echo "Rebuilding containers..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    ;;
  *)
    echo "Usage: $0 {start|start-with-workers|stop|restart|logs|migrate|makemigrations|createsuperuser|shell|init-search|seed-products|test|clean|rebuild}"
    echo ""
    echo "Commands:"
    echo "  start              - Start all services"
    echo "  start-with-workers - Start all services including workers"
    echo "  stop               - Stop all services"
    echo "  restart            - Restart all services"
    echo "  logs [service]     - View logs (default: backend)"
    echo "  migrate            - Run database migrations"
    echo "  makemigrations     - Create new migrations"
    echo "  createsuperuser    - Create Django superuser"
    echo "  shell              - Open Django shell"
    echo "  init-search        - Initialize Elasticsearch index"
    echo "  seed-products      - Add demo products to database"
    echo "  test               - Run tests"
    echo "  clean              - Remove all containers and volumes"
    echo "  rebuild            - Rebuild all containers from scratch"
    exit 1
    ;;
esac
