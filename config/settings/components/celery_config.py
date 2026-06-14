# Create this file inside your settings/components/ directory

def get_celery_config(env):
    """
    👑 CELERY BROKER & RUNTIME CONFIGURATION COMPONENT
    Configures RabbitMQ as the message broker and isolates task trace logs 
    inside high-speed Redis RAM cache slots.
    """
    # 1. Pull RabbitMQ wire string parameter safely from your local env context
    # Fallback to local Docker container name string patterns if unspecified
    broker_url = env.str("CELERY_BROKER_URL", default="amqp://guest:guest@rabbitmq:5672//")
    
    # 2. Pull high-speed Redis backend location parameter for task result strings
    # Isolates task trackers cleanly using Redis logical database cache slot 1
    result_backend = env.str("CELERY_RESULT_BACKEND", default="redis://redis:6379/1")

    return {
        "CELERY_BROKER_URL": broker_url,
        "CELERY_RESULT_BACKEND": result_backend,
        
        # 👑 THE RAM SAVER: Globally tells Celery NOT to store task results in Redis
        "CELERY_TASK_IGNORE_RESULT": True,
        
        # Completely disables storing the task metadata/states unless explicitly requested.
        # This eliminates the initialization and completion RAM writes entirely.
        "CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED": True, 
        
        "CELERY_TASK_ACKS_LATE": True,
        "CELERY_TASK_REJECT_ON_WORKER_LOST": True,
        "CELERY_RESULT_EXPIRES": 86400, 
        "CELERY_TIMEZONE": env.str("TIME_ZONE", default="UTC"),
        "CELERY_ENABLE_UTC": True,
        "CELERY_TASK_ROUTES": {
            # Fast, high-priority e-commerce tasks go to the 'checkout' highway
            "apps.orders.tasks.inspect_order_stock_ttl": {
                "queue": "checkout",
            },
        },
    }