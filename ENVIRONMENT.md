# Environment Configuration Guide

This document explains how to configure the Pyrox application using environment variables.

## Quick Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your specific configuration values

3. For production deployments, use:
   ```bash
   cp .env.production .env
   ```

## Environment Files

- **`.env`** - Your local configuration (DO NOT commit to git)
- **`.env.example`** - Example configuration (safe to commit)
- **`.env.production`** - Production template (uses environment variables for secrets)

## Key Configuration Sections

### Application Core
- `PYROX_DEBUG` - Enable/disable debug mode
- `PYROX_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `PYROX_ENVIRONMENT` - Current environment (development, staging, production)

### Database
- `DATABASE_URL` - Database connection string
- `DATABASE_DEBUG` - Enable SQL query logging
- `DATABASE_POOL_SIZE` - Connection pool size

### Security
- `SECRET_KEY` - Application secret key (change in production!)
- `JWT_SECRET_KEY` - JWT signing key
- `PASSWORD_MIN_LENGTH` - Minimum password length

### PLC Integration
- `PLC_DEFAULT_CONTROLLER_TYPE` - Default PLC controller type
- `PLC_COMMUNICATION_TIMEOUT` - Communication timeout in milliseconds
- `PLC_DEFAULT_IP` - Default PLC IP address

### EPLAN Integration
- `EPLAN_DEFAULT_PROJECT_DIR` - Default project directory
- `EPLAN_SUPPORTED_FORMATS` - Supported file formats
- `EPLAN_IMPORT_TIMEOUT` - Import timeout in seconds

### UI Configuration
- `UI_THEME` - Application theme
- `UI_WINDOW_SIZE` - Default window size
- `UI_AUTO_SAVE` - Enable auto-save functionality

## Production Deployment

For production environments:

1. Use strong, unique secret keys
2. Set `PYROX_DEBUG=false`
3. Use appropriate log levels (WARNING or ERROR)
4. Configure proper database connections
5. Enable monitoring and health checks
6. Set up proper backup strategies

## Security Considerations

- Never commit `.env` files to version control
- Use environment variables for sensitive data in production
- Rotate secret keys regularly
- Use SSL/TLS in production environments
- Enable audit logging for compliance

## Environment Variable Substitution

The application supports variable substitution:
- `${VAR}` - Substitute environment variable
- `$VAR` - Simple variable substitution

Example:
```bash
BASE_DIR=/opt/pyrox
DATA_DIR=${BASE_DIR}/data
```

## Validation

The application will validate environment variables on startup and log warnings for:
- Missing required variables
- Invalid values
- Security concerns (weak secrets, debug mode in production)

## Support

For questions about environment configuration, contact:
Brian LaFond <Brian.L.LaFond@gmail.com>