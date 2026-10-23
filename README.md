# Production-Style Spring Boot Application Repository for Harness CI

[![Java](https://img.shields.io/badge/Java-25%20LTS%20(Release%2021%20Bytecode)-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.4.2-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Build Tool](https://img.shields.io/badge/Maven-3.9+-C71A36.svg)](https://maven.apache.org/)
[![Container](https://img.shields.io/badge/Docker-Multi--Stage%20Hardened-blue.svg)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/Harness%20CI-Pipeline%20YAML-00ADEF.svg)](https://harness.io/)

A production-grade, enterprise-architected Spring Boot microservice designed specifically as a reference and hands-on repository for mastering **Harness Continuous Integration (Harness CI)**.

---

## Table of Contents

1. [Architecture & Design Principles](#1-architecture--design-principles)
2. [Repository Structure](#2-repository-structure)
3. [Local Windows 11 Setup Guide](#3-local-windows-11-setup-guide)
4. [Local Build & Test Commands](#4-local-build--test-commands)
5. [Docker Build & Run Commands](#5-docker-build--run-commands)
6. [Harness CI Setup & Configuration Guide](#6-harness-ci-setup--configuration-guide)
   - [Harness UI Project Setup](#harness-ui-project-setup)
   - [Secret Management](#secret-management)
   - [Connector Configuration](#connector-configuration)
   - [Pipeline Import Instructions](#pipeline-import-instructions)
   - [Webhook Trigger Setup](#webhook-trigger-setup)
7. [Comprehensive Test Plan](#7-comprehensive-test-plan)
   - [Test Case 1: Proving a Failed Test Prevents Image Publication](#test-case-1-proving-a-failed-test-prevents-image-publication)
   - [Test Case 2: Proving Successful Execution Publishes an Immutable SHA Tag](#test-case-2-proving-successful-execution-publishes-an-immutable-sha-tag)
8. [Troubleshooting Guide](#8-troubleshooting-guide)

---

## 1. Architecture & Design Principles

```
+---------------------------------------------------------------------------------------------------+
|                                      HARNESS CI PIPELINE                                          |
|                                                                                                   |
|  +--------------------+     +---------------------+     +--------------------------------------+  |
|  |   Source Clone     | ==> | Build & Verify Tests| ==> |      Containerize & Publish          |  |
|  |  (Git Connector)   |     |  - Compile Source   |     |  - Multi-stage Docker Build          |  |
|  |                    |     |  - Surefire (Unit)  |     |  - Tag with Commit SHA & latest      |  |
|  |                    |     |  - Failsafe (IT)    |     |  - Push to Docker Hub Registry       |  |
|  +--------------------+     +---------------------+     +--------------------------------------+  |
|                                        |                                   |                      |
|                                        v (If Tests Fail)                   v (If Tests Pass)      |
|                               +-----------------+                 +-------------------+           |
|                               |  ABORT PIPELINE |                 |  IMMUTABLE IMAGE  |           |
|                               |  (Zero Artifact |                 |  PUBLISHED TO     |           |
|                               |     Published)  |                 |  REGISTRY WITH    |           |
|                               +-----------------+                 |  COMMIT SHA TAG   |           |
|                                                                   +-------------------+           |
+---------------------------------------------------------------------------------------------------+
```

### Application Design Highlights
- **Framework & Runtime:** Spring Boot 3.4.2 running on **Java 25 LTS** with `--release 21` bytecode compilation for full ASM and ByteBuddy runtime stability.
- **REST CRUD API:** Complete employee management (`/api/v1/employees`) supporting JSON payloads, URI Location headers on creation, pagination-ready structure, and HTTP 204 No Content deletions.
- **Robust Validation:** JSR-380 Bean Validation (`@NotBlank`, `@Email`, `@NotNull`, `@PositiveOrZero`, `@Size`) with standardized RFC 7807 problem details in `GlobalExceptionHandler`.
- **Health Checks:** Built-in Spring Boot Actuator (`/actuator/health`, `/actuator/info`) plus dedicated `/api/v1/health` endpoint reporting uptime, service identifier, and Java version.
- **Structured Logging:** Logback configured with ISO 8601 timestamps, log level, thread ID, logger names, and **MDC Correlation ID** (`X-Correlation-Id`) tracking across every request and response.
- **In-Memory Thread-Safe Persistence:** Concurrent storage with pre-seeded demo records (`Sarah Connor`, `John Doe`, `Alex Murphy`), eliminating external database spin-up latency during CI runs.
- **Fail-Fast Testing Strategy:** Maven Surefire and Failsafe plugins enforce `<testFailureIgnore>false</testFailureIgnore>`, halting the build immediately upon test regression.
- **Production-Hardened Container:**
  - Multi-stage build (Builder: Maven 3.9 + Temurin 21; Runtime: Temurin 21 JRE Alpine).
  - Enforced non-root user (`appuser:appgroup`, UID 10001).
  - Native Docker `HEALTHCHECK` hitting `/actuator/health`.
  - Cgroup-aware container JVM parameters (`-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0`).

---

## 2. Repository Structure

```
.
├── .dockerignore                            # Excludes git, target, logs from container context
├── .github/
│   └── workflows/
│       └── ci.yml                           # Optional reference GitHub Actions workflow
├── .gitignore                               # Standard Git ignore file
├── .harness/
│   └── pipeline.yaml                        # Production Harness CI Pipeline definition
├── Dockerfile                               # Multi-stage, hardened, non-root container build
├── pom.xml                                  # Maven project configuration (Surefire + Failsafe)
├── README.md                                # This comprehensive documentation
└── src/
    ├── main/
    │   ├── java/com/harness/demo/
    │   │   ├── EmployeeServiceApplication.java   # Spring Boot entry point
    │   │   ├── controller/
    │   │   │   └── EmployeeController.java       # REST endpoints (CRUD + /health)
    │   │   ├── dto/
    │   │   │   ├── EmployeeRequest.java          # Validated input record
    │   │   │   ├── EmployeeResponse.java         # API output record
    │   │   │   └── ErrorResponse.java            # Structured error representation
    │   │   ├── exception/
    │   │   │   ├── DuplicateResourceException.java
    │   │   │   ├── GlobalExceptionHandler.java   # Centralized @RestControllerAdvice
    │   │   │   └── ResourceNotFoundException.java
    │   │   ├── filter/
    │   │   │   └── CorrelationIdFilter.java      # MDC correlation tracking filter
    │   │   ├── model/
    │   │   │   └── Employee.java                 # Core domain entity
    │   │   ├── repository/
    │   │   │   └── EmployeeRepository.java       # Thread-safe in-memory store
    │   │   └── service/
    │   │       └── EmployeeService.java          # Business logic & validation
    │   └── resources/
    │       ├── application.yml                   # Actuator & application properties
    │       └── logback-spring.xml                # Structured console logging configuration
    └── test/
        └── java/com/harness/demo/
            ├── EmployeeServiceApplicationIT.java # Failsafe integration tests (full stack)
            ├── FailTestGateDemoTest.java         # Test gate verification utility
            ├── controller/
            │   └── EmployeeControllerTest.java   # WebMvc unit tests (MockMvc)
            └── service/
                └── EmployeeServiceTest.java      # Isolated service unit tests (Mockito)
```

---

## 3. Local Windows 11 Setup Guide

### Prerequisites
Ensure the following tools are installed on your Windows 11 workstation:
1. **Oracle JDK 25 LTS** (or JDK 21+): [Oracle Java Downloads](https://www.oracle.com/java/technologies/downloads/)
2. **Apache Maven 3.9+**: [Maven Downloads](https://maven.apache.org/download.cgi)
3. **Docker Desktop for Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with WSL2 backend enabled)
4. **Git for Windows**: [Git SCM](https://git-scm.com/)

### Step 1: Open PowerShell as Administrator or Standard User
Verify tool installations:
```powershell
# Verify Java version (shows Java 25 or 21)
java -version

# Verify Maven version
mvn -version

# Verify Docker CLI
docker --version

# Verify Git version
git --version
```

### Step 2: Clone or Open Repository
```powershell
cd C:\Users\Naresh\Documents\GitHub\Harness-Projects
git status
```

---

## 4. Local Build & Test Commands

### Run Compilation Only
```powershell
mvn clean compile
```

### Run Unit Tests (Surefire)
Executes all unit tests (`*Test.java`), mocking dependencies with Mockito:
```powershell
mvn test
```
*Expected Output:*
```
[INFO] Running com.harness.demo.controller.EmployeeControllerTest
[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.harness.demo.service.EmployeeServiceTest
[INFO] Tests run: 9, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.harness.demo.FailTestGateDemoTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

### Run Integration Tests (Failsafe)
Boots the full Spring Boot application context on a random port, validating live HTTP endpoints and database state:
```powershell
mvn verify "-DskipUnitTests=true"
```
*Expected Output:*
```
[INFO] Running com.harness.demo.EmployeeServiceApplicationIT
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

### Run Full Test Suite (Unit + Integration + Packaging)
```powershell
mvn clean verify
```

### Run Application Locally
```powershell
mvn spring-boot:run
```
The application will start on `http://localhost:8080`.

### Test Endpoints via PowerShell or cURL

#### 1. Check Application Health
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/actuator/health" -Method Get | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/health" -Method Get | ConvertTo-Json
```

#### 2. List All Pre-Seeded Employees
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/employees" -Method Get | ConvertTo-Json
```

#### 3. Create a New Employee (Validation Enforced)
```powershell
$body = @{
    firstName  = "Grace"
    lastName   = "Hopper"
    email      = "grace.hopper@navy.mil"
    department = "Compilers"
    salary     = 175000.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/api/v1/employees" `
    -Method Post `
    -Headers @{"Content-Type" = "application/json"} `
    -Body $body | ConvertTo-Json
```

#### 4. Fetch Employee by ID
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/employees/1001" -Method Get | ConvertTo-Json
```

#### 5. Update Employee
```powershell
$updateBody = @{
    firstName  = "Grace"
    lastName   = "Hopper"
    email      = "grace.hopper@navy.mil"
    department = "Compiler Engineering"
    salary     = 185000.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/api/v1/employees/1004" `
    -Method Put `
    -Headers @{"Content-Type" = "application/json"} `
    -Body $updateBody | ConvertTo-Json
```

#### 6. Delete Employee
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/v1/employees/1004" -Method Delete
```

#### 7. Verify Validation Failure (HTTP 400)
```powershell
$invalidBody = @{
    firstName = ""
    lastName  = ""
    email     = "not-valid"
    department= ""
    salary    = -500
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "http://localhost:8080/api/v1/employees" `
        -Method Post `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $invalidBody
} catch {
    $_.ErrorDetails.Message
}
```

---

## 5. Docker Build & Run Commands

> **Important:** Ensure Docker Desktop is running before executing container commands.

### Build the Multi-Stage Production Image Locally
```powershell
docker build -t employee-service:local .
```

### Run the Container
```powershell
docker run -d --name employee-app -p 8080:8080 employee-service:local
```

### Verify Container Health & Non-Root Execution
```powershell
# 1. View logs
docker logs employee-app

# 2. Check running process user (proves non-root execution UID 10001)
docker exec employee-app whoami
# Output: appuser

# 3. Check container health status evaluated by Docker Engine
docker inspect --format='{{json .State.Health.Status}}' employee-app
# Output: "healthy"
```

### Cleanup Local Container
```powershell
docker stop employee-app
docker rm employee-app
```

---

## 6. Harness CI Setup & Configuration Guide

Harness CI provides an automated, resilient, and enterprise-grade execution platform. Follow these steps to configure your project, connectors, secrets, and pipeline.

### Harness UI Project Setup
1. Log in to [app.harness.io](https://app.harness.io).
2. Select your **Account** and **Organization** (e.g., `default`).
3. Click **Projects** ➔ **New Project**:
   - **Name:** `Harness CI Showcase`
   - **Identifier:** `default_project` (or your preferred ID).

---

### Secret Management
Never store plaintext credentials or tokens in pipeline YAML or Git. Create the following Harness Secrets:

Navigate to **Project Settings** ➔ **Secrets** ➔ **+ New Secret** ➔ **Secret Text**:

| Secret Name | Identifier | Secret Value Description | Scope |
| :--- | :--- | :--- | :--- |
| `Docker Hub Username` | `dockerhub_username` | Your Docker Hub account username (e.g., `johndoe`) | Project |
| `Docker Hub Token` | `dockerhub_token` | Docker Hub Personal Access Token (PAT) with `Read & Write` scope | Project |
| `GitHub PAT` | `github_pat` | GitHub Personal Access Token with `repo` and `admin:repo_hook` scopes | Project |

*Reference in Pipeline:*
- Secrets are securely resolved at runtime: `<+secrets.getValue("dockerhub_token")>`

---

### Connector Configuration

Connectors provide authenticated integration links to third-party tools.

#### 1. GitHub Codebase Connector (`github_connector`)
Navigate to **Project Settings** ➔ **Connectors** ➔ **+ New Connector** ➔ **Code Repositories** ➔ **GitHub**:
- **Name:** `GitHub Connector`
- **Identifier:** `github_connector`
- **URL Type:** `Repository`
- **Connection Type:** `HTTP`
- **Repository URL:** `https://github.com/<your-github-username>/employee-service`
- **Authentication:**
  - **Username:** Your GitHub username
  - **Personal Access Token:** Select Secret `<+secrets.getValue("github_pat")>`
- **Connectivity Mode:** `Connect through Harness Platform` (Harness Cloud)
- Click **Save and Test** to verify connection.

#### 2. Docker Hub Registry Connector (`dockerhub_connector`)
Navigate to **Project Settings** ➔ **Connectors** ➔ **+ New Connector** ➔ **Artifact Repositories** ➔ **Docker Registry**:
- **Name:** `Docker Hub Connector`
- **Identifier:** `dockerhub_connector`
- **Docker Registry URL:** `https://index.docker.io/v1/`
- **Provider Type:** `Docker Hub`
- **Authentication:**
  - **Username:** Select Secret `<+secrets.getValue("dockerhub_username")>` or enter username
  - **Password:** Select Secret `<+secrets.getValue("dockerhub_token")>`
- **Connectivity Mode:** `Connect through Harness Platform`
- Click **Save and Test** to verify connection.

---

### Pipeline Import Instructions

You can import the pipeline definition using either **Git Experience** or the **Harness Pipeline Studio**:

#### Method A: Direct YAML Paste in Harness Studio
1. In your Harness Project, navigate to **Pipelines** ➔ **+ Create a Pipeline**.
2. Name: `employee-service-ci`, Identifier: `employeeserviceci`.
3. In the top right corner of the Studio canvas, toggle from **Visual** to **YAML**.
4. Open `.harness/pipeline.yaml` from this repository, copy its entire contents, and paste it into the editor.
5. Click **Save**.

#### Method B: Harness Git Experience (Recommended for Production)
1. In **Pipelines**, click **Create Pipeline** ➔ Select **Store in Git**.
2. Select Connector: `github_connector`.
3. Repository: `employee-service`.
4. Git Branch: `main`.
5. File Path: `.harness/pipeline.yaml`.
6. Harness will bi-directionally sync the pipeline with your Git commits.

---

### Webhook Trigger Setup

Configure automatic pipeline execution when developers push code or open pull requests:

1. In your pipeline, click **Triggers** (in the top navigation bar).
2. Click **+ New Trigger** ➔ Select **GitHub**.
3. **Trigger Name:** `On Push to Main`.
4. **Connector:** `github_connector`.
5. **Event:** Select **Push**.
6. **Conditions (Build Execution):**
   - Branch Name: `equals` ➔ `main`
7. **Pipeline Input:**
   - `build`: `<+trigger.commitSha>`
   - `dockerhub_username`: Your Docker Hub username
8. Click **Create Trigger**.
9. Harness automatically registers the webhook in your GitHub repository settings.

---

## 7. Comprehensive Test Plan

This test plan provides verifiable proof of two critical CI/CD safety requirements:
1. **A failed test strictly halts the pipeline, preventing containerization and publication.**
2. **A successful test run automatically builds and publishes an immutable, SHA-tagged image.**

---

### Test Case 1: Proving a Failed Test Prevents Image Publication

#### Objective
Prove that any unit or integration test regression triggers Maven build failure (exit code 1), causing Harness CI to abort immediately and **never publish an image to Docker Hub**.

#### Execution Steps (Simulated or Live in CI)
1. Run the test gate verification utility with failure flag enabled:
   ```powershell
   mvn test "-Dtest=FailTestGateDemoTest" "-Dfail.ci.build=true"
   ```
2. **Observed Maven Output:**
   ```
   [ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0 <<< FAILURE!
   org.opentest4j.AssertionFailedError: PROVING CI FAILURE GATE: System property 'fail.ci.build' was set to true.
   Maven build is terminated immediately, preventing artifact packaging and container publication.
   [INFO] BUILD FAILURE
   ```
3. **Harness CI Stage Behavior:**
   - **Stage 1 (Build and Verify Tests):** Step `run_unit_tests` fails with status `FAILED`.
   - **Stage 2 (Containerize and Publish):** Status is `SKIPPED` / `NOT RUN`.
   - **Registry Check:** Inspect Docker Hub repository. **No new image tag or build artifact is pushed.**
4. **Conclusion:** Broken builds cannot escape the CI boundary.

---

### Test Case 2: Proving Successful Execution Publishes an Immutable SHA Tag

#### Objective
Prove that when all tests pass, the pipeline tags the Docker container with the exact Git commit SHA (`<+codebase.commitSha>`), ensuring complete traceability and immutability.

#### Execution Steps
1. Run the test suite normally:
   ```powershell
   mvn test "-Dtest=FailTestGateDemoTest"
   ```
   *Result: `BUILD SUCCESS` (Exit code 0).*
2. Commit and push changes to the repository:
   ```powershell
   git rev-parse HEAD
   # Example output: 7c8a14b2d9e6f3a1...
   ```
3. Harness CI executes:
   - **Stage 1 (Build and Verify Tests):**
     - `compile_source` ➔ Succeeded.
     - `run_unit_tests` ➔ Succeeded (16 tests passed).
     - `run_integration_tests` ➔ Succeeded (5 integration tests passed).
   - **Stage 2 (Containerize and Publish):**
     - Step `build_and_push_docker_hub` builds the multi-stage Dockerfile.
     - Dynamic tags resolved:
       - `<username>/employee-service:7c8a14b2d9e6f3a1...` (Immutable SHA Tag)
       - `<username>/employee-service:latest`
     - Pushes both tags to Docker Hub.
4. **Verification via Docker CLI:**
   ```powershell
   # Pull specifically by immutable Commit SHA tag
   docker pull <your-dockerhub-username>/employee-service:<commit-sha>
   ```
5. **Conclusion:** Production releases are cryptographically and verifiably bound to the exact Git commit SHA that passed all test quality gates.

---

## 8. Troubleshooting Guide

| Issue / Error Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| `Cannot connect to Docker daemon` | Docker Desktop is not started on Windows 11. | Launch Docker Desktop from the Start menu and wait until the status displays "Engine running". |
| `Java 25 (69) is not supported by Byte Buddy` | ByteBuddy agent running on JDK 25 without experimental flag. | Pass `-Dnet.bytebuddy.experimental=true` in `argLine` (already configured in `pom.xml`). |
| `ASM ClassReader failed to parse class file` | Spring Framework attempting to scan Java 25 bytecode. | Keep `maven.compiler.release` set to `21` in `pom.xml` so bytecode is 100% compatible with Spring Boot 3.4.2 while running on JDK 25. |
| Harness step fails: `Connector github_connector not found` | The identifier in `pipeline.yaml` doesn't match the connector in Harness UI. | Ensure the connector identifier in Harness Project Settings is exactly `github_connector`. |
| Harness step fails: `denied: requested access to the resource is denied` | Docker Hub token lacks write permissions or username mismatch. | Verify the Docker Hub Personal Access Token has `Read, Write, Delete` permissions and secret `dockerhub_username` matches the repository namespace. |
| PowerShell argument parse error on `-D` flags | PowerShell treats `-Dproperty=value` as an operator. | Always wrap Java/Maven system properties in double quotes: `mvn test "-Dfail.ci.build=true"`. |

---

## License & Attribution

Distributed under the Apache 2.0 License. Designed for DevOps engineers, SREs, and cloud architects learning enterprise CI/CD with Harness.
