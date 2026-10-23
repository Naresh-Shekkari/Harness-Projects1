# ==============================================================================
# Multi-Stage Production Dockerfile for Employee Service
# Stage 1: Build & Strict Test Verification
# Stage 2: Hardened Minimal JRE Runtime
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Package
# ------------------------------------------------------------------------------
FROM maven:3.9.9-eclipse-temurin-21-alpine AS builder

WORKDIR /build

# Cache dependencies layer
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy application source code
COPY src ./src

# Execute compilation, unit tests, and packaging.
# Note: Fails immediately if any test fails, safeguarding artifact integrity.
RUN mvn clean package -DskipTests=false -Dnet.bytebuddy.experimental=true

# ------------------------------------------------------------------------------
# Stage 2: Production Hardened Minimal Runtime
# ------------------------------------------------------------------------------
FROM eclipse-temurin:21-jre-alpine AS runtime

LABEL maintainer="DevOps Team <devops@example.com>"
LABEL service="employee-service"
LABEL description="Production hardened Spring Boot REST API for Harness CI Showcase"

# Create a non-root dedicated application group and user (UID/GID: 10001)
RUN addgroup -S -g 10001 appgroup && \
    adduser -S -u 10001 -G appgroup -s /sbin/nologin -h /app appuser

WORKDIR /app

# Copy packaged jar from builder stage with proper non-root ownership
COPY --from=builder --chown=appuser:appgroup /build/target/employee-service-*.jar /app/app.jar

# Enforce non-root execution
USER 10001:10001

# Expose HTTP port
EXPOSE 8080

# Configure production health check against Spring Boot Actuator
HEALTHCHECK --interval=30s --timeout=3s --retries=3 --start-period=20s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# Production JVM options optimized for Linux container memory cgroups
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:InitialRAMPercentage=50.0 -Djava.security.egd=file:/dev/./urandom"

ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
