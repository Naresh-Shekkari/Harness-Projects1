# Production-Style Spring Boot Application Repository for Harness CI

[![Java](https://img.shields.io/badge/Java-25%20LTS-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.5+-brightgreen.svg)](https://spring.io/projects/spring-boot)
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
6. [Harness CI Setup & Configuration Guide (Complete Beginner Walkthrough)](#6-harness-ci-setup--configuration-guide)
   - [6.0 Core Harness Concepts Explained](#60-core-harness-concepts-explained)
   - [6.1 Gathering External Tokens (GitHub & Docker Hub)](#61-gathering-external-tokens-github--docker-hub)
   - [6.2 Creating Account, Organization & Project in Harness UI](#62-creating-account-organization--project-in-harness-ui)
   - [6.3 Creating Secrets in Harness UI](#63-creating-secrets-in-harness-ui)
   - [6.4 Creating Connectors in Harness UI](#64-creating-connectors-in-harness-ui)
   - [6.5 Importing & Saving the Pipeline](#65-importing--saving-the-pipeline)
   - [6.6 Configuring the Git Push Webhook Trigger](#66-configuring-the-git-push-webhook-trigger)
   - [6.7 Running & Verifying the Pipeline](#67-running--verifying-the-pipeline)
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
- **Framework & Runtime:** Spring Boot running on **Java 25 LTS** with `--release 21` bytecode compilation for full ASM and ByteBuddy runtime stability.
- **REST CRUD API:** Complete employee management (`/api/v1/employees`) supporting JSON payloads, URI Location headers on creation, pagination-ready structure, and HTTP 204 No Content deletions.
- **Robust Validation:** JSR-380 Bean Validation (`@NotBlank`, `@Email`, `@NotNull`, `@PositiveOrZero`, `@Size`) with standardized RFC 7807 problem details in `GlobalExceptionHandler`.
- **Health Checks:** Built-in Spring Boot Actuator (`/actuator/health`, `/actuator/info`) plus dedicated `/api/v1/health` endpoint reporting uptime, service identifier, and Java version.
- **Structured Logging:** Logback configured with ISO 8601 timestamps, log level, thread ID, logger names, and **MDC Correlation ID** (`X-Correlation-Id`) tracking across every request and response.
- **In-Memory Thread-Safe Persistence:** Concurrent storage with pre-seeded demo records (`Sarah Connor`, `John Doe`, `Alex Murphy`), eliminating external database spin-up latency during CI runs.
- **Fail-Fast Testing Strategy:** Maven Surefire and Failsafe plugins enforce `<testFailureIgnore>false</testFailureIgnore>`, halting the build immediately upon test regression.
- **Production-Hardened Container:**
  - Multi-stage build (Builder: Maven + Temurin 25; Runtime: Temurin 25 JRE Alpine).
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
├── README.md                                # Comprehensive documentation & step-by-step setup guide
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

### Step 1: Open PowerShell
Verify tool installations:
```powershell
# Verify Java version (shows Java 25)
java -version

# Verify Maven version
mvn -version

# Verify Docker CLI
docker --version

# Verify Git version
git --version
```

### Step 2: Open Repository Directory
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

### Run Integration Tests (Failsafe)
Boots the full Spring Boot application context on a random port, validating live HTTP endpoints and database state:
```powershell
mvn verify "-DskipUnitTests=true"
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

### Test Endpoints via PowerShell

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

> **Target Audience:** This section is written for anyone with zero prior Harness experience. Every single screen, click, and field is documented below point-by-point with visual UI layout mockups.

---

### 6.0 Core Harness Concepts Explained

Before opening the browser, understand these 5 core building blocks:

```
  +------------------------------------------------------------------------+
  |  1. ACCOUNT        (Your overarching company or personal tenancy)     |
  |     +------------------------------------------------------------------+
  |     |  2. ORGANIZATION  (Logical group, e.g. "default" or "Engineering")
  |     |     +------------------------------------------------------------+
  |     |     |  3. PROJECT       (Contains pipelines, connectors & secrets)
  |     |     |     +------------------------------------------------------+
  |     |     |     |  4. CONNECTORS  (Secure links to GitHub & Docker Hub)|
  |     |     |     |  5. SECRETS     (Encrypted passwords/tokens)        |
  |     |     |     |  6. PIPELINE    (The workflow that compiles & tests) |
  +-----+-----+-----+-----+------------------------------------------------+
```

1. **Account:** Your top-level container after signing up at [app.harness.io](https://app.harness.io).
2. **Organization:** A group of projects (default name is `default`).
3. **Project:** A dedicated workspace for this repository (`employee-service`).
4. **Connectors:** Authenticated credentials linking Harness to your GitHub repo and Docker Hub.
5. **Pipeline:** The automated multi-stage CI workflow defined in `.harness/pipeline.yaml`.

---

### 6.1 Gathering External Tokens (GitHub & Docker Hub)

You will need **two tokens** ready before setting up Harness. Follow these steps to generate them:

#### Step 6.1.1: Generate GitHub Personal Access Token (PAT)
1. Open your browser and go to: **[github.com/settings/tokens](https://github.com/settings/tokens)**
2. Click **Generate new token** ➔ Select **Generate new token (classic)**.
3. In **Note**, enter: `harness-ci-token`.
4. In **Expiration**, choose `90 days` or your preferred duration.
5. Check the following scopes (checkboxes):
   - [x] **`repo`** *(Full control of private and public repositories)*
   - [x] **`admin:repo_hook`** *(Full control of repository webhooks - required for automatic triggers)*
6. Scroll down and click the green button: **Generate token**.
7. **IMPORTANT:** Copy the token string immediately (e.g., `ghp_xxxxxxxxxxxxxxxxxxxx`). Store it temporarily in a notepad.

#### Step 6.1.2: Generate Docker Hub Personal Access Token (PAT)
1. Open your browser and log in to: **[hub.docker.com](https://hub.docker.com/)**
2. In the top-right corner, click your **Profile Avatar** ➔ Select **Account Settings**.
3. In the left navigation menu, click **Security**.
4. Click the blue button: **New Access Token**.
5. In **Access Token Description**, type: `harness-docker-token`.
6. In **Access permissions**, select: **Read, Write, Delete**.
7. Click **Generate**.
8. **IMPORTANT:** Copy the generated token string immediately (e.g., `dckr_pat_xxxxxxxxxxxxxxxxxxxx`). Note down your **Docker Hub Username** as well.

---

### 6.2 Creating Account, Organization & Project in Harness UI

#### Step 1: Log in to Harness
1. Navigate to: **[https://app.harness.io](https://app.harness.io)**
2. Sign in with your work email, Google, or GitHub account.
3. You will land on the Harness Home Dashboard.

#### Step 2: Navigate to Projects
In the top-left breadcrumb menu, ensure your **Organization** is selected (or click **All Projects**).

```
+-----------------------------------------------------------------------------------------+
| [Harness Logo]  Account: MyAccount  /  Org: default  /  Projects                        |
+-----------------------------------------------------------------------------------------+
|  Projects                                                             [+ New Project]   |
|  Search projects...                                                                     |
|                                                                                         |
|  [Default Project]       [Project Alpha]                                                |
+-----------------------------------------------------------------------------------------+
```

#### Step 3: Create a New Project
1. In the top-right corner, click the blue button: **`+ New Project`**.
2. A slide-out panel titled **Create a Project** will appear on the right side of the screen:

```
+-----------------------------------------------------------------+
| Create a Project                                            [X] |
+-----------------------------------------------------------------+
| Name *                                                          |
| [ Harness CI Showcase                                      ]    |
|                                                                 |
| Identifier                                                      |
| [ default_project                                         ]     |
| (Click edit icon if you want to set a custom identifier)        |
|                                                                 |
| Description                                                     |
| [ Learning and mastering Harness CI with Spring Boot       ]    |
|                                                                 |
| Tags                                                            |
| [ Key: environment ] [ Value: learning ]                        |
|                                                                 |
| Color                                                           |
| (Pick any color dot)                                            |
|                                                                 |
|                                       [Cancel]  [Save and Continue]
+-----------------------------------------------------------------+
```

3. Fill out the fields:
   - **Name:** `Harness CI Showcase`
   - **Identifier:** `default_project` *(Note: If your identifier auto-generates as `Harness_CI_Showcase`, click the small pencil icon next to Identifier and change it to `default_project` to match `.harness/pipeline.yaml`)*
   - **Description:** `Learning and mastering Harness CI with Spring Boot`
4. Click the blue button: **Save and Continue**.

#### Step 4: Enable the Continuous Integration Module
1. On the next screen, you will be asked to invite collaborators. Click **Continue** (or skip).
2. You will now see the Harness Modules screen:

```
+-----------------------------------------------------------------------------------------+
| Select Module to start                                                                  |
+-----------------------------------------------------------------------------------------+
|  +---------------------------+   +---------------------------+                          |
|  | [CI Icon]                 |   | [CD Icon]                 |                          |
|  | Continuous Integration    |   | Continuous Delivery       |                          |
|  | Build, test and package   |   | Automate deployments      |                          |
|  | [Explore Module ->]       |   |                           |                          |
|  +---------------------------+   +---------------------------+                          |
+-----------------------------------------------------------------------------------------+
```

3. Click **Continuous Integration** (or **Explore Module** under Continuous Integration).
4. You are now inside your Project workspace!

---

### 6.3 Creating Secrets in Harness UI

We will now store the credentials safely so the pipeline can access them securely.

Navigate to: **Project Settings** (bottom-left gear icon or left navigation bar) ➔ Under **Security**, click **Secrets**.

```
+-----------------------------------------------------------------------------------------+
| Project: Harness CI Showcase  >  Project Settings  >  Secrets                           |
+-----------------------------------------------------------------------------------------+
| Secrets                                                            [+ New Secret v]     |
| [Search Secrets...      ]                                                               |
+-----------------------------------------------------------------------------------------+
```

Click the blue button: **`+ New Secret`** ➔ Click **`Secret Text`**.

#### Secret 1: `github_pat`
Fill in the form:
- **Secret Name:** `GitHub PAT`
- **Secret Identifier:** Click the pencil icon and verify it is: `github_pat`
- **Secret Value:** Paste your GitHub Personal Access Token generated in Step 6.1.1 (`ghp_...`).
- Click **Save**.

```
+-----------------------------------------------------------------+
| Add Secret Text                                             [X] |
+-----------------------------------------------------------------+
| Secret Name *                                                   |
| [ GitHub PAT                                               ]    |
|                                                                 |
| Secret Identifier                                               |
| [ github_pat                                              ]     |
|                                                                 |
| Secret Value *                                                  |
| [ ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx ]            |
|                                                                 |
| Description                                                     |
| [ GitHub Personal Access Token with repo and hook scope    ]    |
|                                                                 |
|                                                [Cancel]  [Save] |
+-----------------------------------------------------------------+
```

#### Secret 2: `dockerhub_token`
Click **`+ New Secret`** ➔ **`Secret Text`**:
- **Secret Name:** `Docker Hub Token`
- **Secret Identifier:** Click pencil icon and set to: `dockerhub_token`
- **Secret Value:** Paste your Docker Hub Access Token generated in Step 6.1.2 (`dckr_pat_...`).
- Click **Save**.

#### Secret 3: `dockerhub_username`
Click **`+ New Secret`** ➔ **`Secret Text`**:
- **Secret Name:** `Docker Hub Username`
- **Secret Identifier:** Click pencil icon and set to: `dockerhub_username`
- **Secret Value:** Enter your exact Docker Hub username (e.g. `johndoe`).
- Click **Save**.

*Verification:* Your Secrets table should now show 3 secrets: `github_pat`, `dockerhub_token`, and `dockerhub_username`.

---

### 6.4 Creating Connectors in Harness UI

Connectors tell Harness how to talk to GitHub and Docker Hub.

Navigate to: **Project Settings** (gear icon) ➔ Under **Security and Connectors**, click **Connectors**.

```
+-----------------------------------------------------------------------------------------+
| Project: Harness CI Showcase  >  Project Settings  >  Connectors                        |
+-----------------------------------------------------------------------------------------+
| Connectors                                                      [+ New Connector]       |
+-----------------------------------------------------------------------------------------+
```

Click the blue button: **`+ New Connector`**.

---

#### Connector 1: GitHub Connector (`github_connector`)

```
+-----------------------------------------------------------------------------------------+
| Select Connector Type                                                               [X] |
+-----------------------------------------------------------------------------------------+
| Code Repositories                                                                       |
|  [ GitHub ]    [ GitLab ]    [ Bitbucket ]    [ Git ]                                   |
+-----------------------------------------------------------------------------------------+
```

1. Under **Code Repositories**, click **GitHub**.
2. **Overview Screen:**
   - **Name:** `GitHub Connector`
   - **Identifier:** Set to `github_connector`
   - Click **Continue**.
3. **Details Screen:**
   - **URL Type:** Select radio button `Repository`.
   - **Connection Type:** Select radio button `HTTP`.
   - **GitHub Repository URL:** Enter your repository URL (e.g., `https://github.com/your-username/Harness-Projects`).
   - Click **Continue**.
4. **Credentials Screen:**
   - **Authentication:** Select `Username and Token`.
   - **Username:** Enter your GitHub username.
   - **Personal Access Token:** Click the dropdown ➔ Select **Existing Secret** ➔ Pick `github_pat`.
   - Click **Continue**.
5. **Connectivity Mode Screen:**
   - Select radio button: **`Connect through Harness Platform`** (This uses Harness Cloud runners; no local delegate installation required!).
   - Click **Save and Test**.
6. **Connection Test:**
   - Harness will make a live handshake with GitHub.
   - You should see a green checkmark: `Connection Successful`.
   - Click **Finish**.

---

#### Connector 2: Docker Hub Connector (`dockerhub_connector`)

1. In the Connectors page, click **`+ New Connector`**.
2. Scroll to **Artifact Repositories** ➔ Click **Docker Registry**.

```
+-----------------------------------------------------------------------------------------+
| Select Connector Type                                                               [X] |
+-----------------------------------------------------------------------------------------+
| Artifact Repositories                                                                   |
|  [ Docker Registry ]    [ Artifactory ]    [ Nexus ]    [ AWS ECR ]                     |
+-----------------------------------------------------------------------------------------+
```

3. **Overview Screen:**
   - **Name:** `Docker Hub Connector`
   - **Identifier:** Set to `dockerhub_connector`
   - Click **Continue**.
4. **Details Screen:**
   - **Docker Registry URL:** Enter `https://index.docker.io/v1/`
   - **Provider Type:** Select `Docker Hub`.
   - **Authentication:** Select `Username and Password`.
   - **Username:** Enter your Docker Hub username (or select secret `dockerhub_username`).
   - **Password / Token:** Click dropdown ➔ Select **Existing Secret** ➔ Pick `dockerhub_token`.
   - Click **Continue**.
5. **Connectivity Mode Screen:**
   - Select radio button: **`Connect through Harness Platform`**.
   - Click **Save and Test**.
6. **Connection Test:**
   - Harness will connect to Docker Hub.
   - You should see a green checkmark: `Connection Successful`.
   - Click **Finish**.

---

### 6.5 Importing & Saving the Pipeline

Now we import the pre-written pipeline definition from `.harness/pipeline.yaml`.

1. In the left navigation bar under **Continuous Integration**, click **Pipelines**.
2. Click the blue button: **`+ Create a Pipeline`**.

```
+-----------------------------------------------------------------------------------------+
| Project: Harness CI Showcase  >  Pipelines                                              |
+-----------------------------------------------------------------------------------------+
| Pipelines                                                       [+ Create a Pipeline]   |
+-----------------------------------------------------------------------------------------+
```

3. **Create Pipeline Dialog:**
   - **Name:** `employee-service-ci`
   - **Identifier:** Click pencil icon and set to `employeeserviceci`
   - **Setup (How do you want to set up your pipeline?):** Select **Inline** (or toggle to YAML).
   - Click **Start**.

```
+-----------------------------------------------------------------+
| Create new Pipeline                                         [X] |
+-----------------------------------------------------------------+
| Name *                                                          |
| [ employee-service-ci                                      ]    |
|                                                                 |
| Identifier                                                      |
| [ employeeserviceci                                       ]     |
|                                                                 |
| Description                                                     |
| [ CI Pipeline for Spring Boot Employee Service             ]    |
|                                                                 |
| Setup:  (*) Inline    ( ) Store in Git                          |
|                                                                 |
|                                                 [Cancel] [Start]|
+-----------------------------------------------------------------+
```

4. You will be taken to the Harness Pipeline Studio canvas.
5. In the top-right corner, find the view toggle: **`[ Visual ]  [ YAML ]`**.
6. Switch from **Visual** to **`YAML`**.

```
+-----------------------------------------------------------------------------------------+
| employee-service-ci                                      [Visual | (YAML)]  [Save] [Run]|
+-----------------------------------------------------------------------------------------+
| 1  pipeline:                                                                            |
| 2    name: employee-service-ci                                                          |
| ...                                                                                     |
+-----------------------------------------------------------------------------------------+
```

7. Select all existing text in the editor and delete it.
8. Open the file **`.harness/pipeline.yaml`** from this repository on your computer.
9. Copy its entire content and paste it into the Harness YAML editor.
10. In the top-right corner, click the blue button: **`Save`**.

*Result:* The pipeline is now saved! You can toggle back to **Visual** to see the interactive diagram showing the two stages:
- **Stage 1: Build and Verify Tests** (`compile_source` ➔ `run_unit_tests` ➔ `run_integration_tests`)
- **Stage 2: Containerize and Publish** (`build_and_push_docker_hub`)

---

### 6.6 Configuring the Git Push Webhook Trigger

To make Harness run automatically every time you push code to GitHub:

1. Inside your pipeline canvas, look at the top navigation tabs: **`[ Pipeline ]  [ Triggers ]  [ Git Experience ]`**.
2. Click **`Triggers`**.

```
+-----------------------------------------------------------------------------------------+
| employee-service-ci  >  Triggers                                                        |
+-----------------------------------------------------------------------------------------+
| Triggers                                                          [+ New Trigger]       |
+-----------------------------------------------------------------------------------------+
```

3. Click **`+ New Trigger`**.
4. Select the **GitHub** tile.
5. **Step 1: Configuration Screen:**
   - **Name:** `On Push to Main`
   - **Description:** `Trigger pipeline automatically on Git push`
   - **Connector:** Select `github_connector`.
   - **Repository:** Enter your GitHub repo name (e.g., `Harness-Projects`).
   - **Event:** In the dropdown, choose **`Push`**.
   - Click **Continue**.

```
+-----------------------------------------------------------------+
| Trigger Configuration                                           |
+-----------------------------------------------------------------+
| Name: [ On Push to Main                                    ]    |
| Connector: [ github_connector                             v ]   |
| Event: [ Push                                             v ]   |
| Actions: [ Any                                            v ]   |
|                                                      [Continue] |
+-----------------------------------------------------------------+
```

6. **Step 2: Conditions (Filters Screen):**
   In this screen, you tell Harness when this trigger should execute (e.g., only when code is pushed to your working branch).

   - **Evaluation Rule:** Keep the default `All conditions must be met (AND)`.
   - **Condition Row:**
     - **Attribute:** In the first dropdown, select **`Branch Name`**.
     - **Operator:** In the second dropdown, select **`Equals`** (or **`In`** if supporting multiple branches).
     - **Matches Value:** Enter your repository's branch name: **`master`** (or `main`).
       > **Note:** Run `git branch --show-current` in your terminal to verify your branch. In this repository, the active branch is `master`.
       > *Tip:* If you want the trigger to run on either `master` or `main`, select Operator **`Regex`** and enter `^(master|main)$`.
   - Click **Continue**.

```
+-----------------------------------------------------------------------------------------+
| Conditions                                                                              |
+-----------------------------------------------------------------------------------------+
| How should conditions be evaluated?                                                     |
| (*) All conditions must be met (AND)      ( ) Any condition can be met (OR)             |
|                                                                                         |
| Attribute                 Operator            Matches Value                             |
| [ Branch Name         v ] [ Equals        v ] [ master                                ] |
|                                                                                         |
| [+ Add Condition]                                                                       |
|                                                                              [Continue] |
+-----------------------------------------------------------------------------------------+
```

7. **Step 3: Pipeline Input (Inputs Screen):**
   This screen configures what values are passed to the pipeline when triggered. It is divided into two sections corresponding to the `<+input>` variables defined in `pipeline.yaml`:

   #### Section A: Codebase / Build
   This determines which commit or branch Harness should clone and build.
   - **If you see "Build Type" options (Radio buttons or Dropdown):**
     - Select **`Commit SHA`** and enter: `<+trigger.commitSha>`
     - *(Alternatively, select **`Git Branch`** and enter: `<+trigger.branch>`)*
   - **If you see a text input field for Branch / Build:**
     - Notice the small value-type toggle icon (e.g., `T`, `fx`, or `<+>`) next to the input field.
     - Click the toggle and choose **`Expression`** (`<+>`).
     - Enter: `<+trigger.commitSha>` (or `<+trigger.branch>`).
   
   > **Why this expression?** `<+trigger.commitSha>` tells Harness to build the exact commit SHA that was pushed in the GitHub webhook payload, ensuring an immutable build.

   #### Section B: Pipeline Variables
   - **`dockerhub_username` (* Required):**
     - Type your actual Docker Hub username (e.g., `johndoe`).
   - **`dockerhub_repo_name`:**
     - Pre-filled with the default: `employee-service` (leave as is, or enter your custom repo name).

   - Click the blue button at the bottom: **`Create Trigger`**.

```
+-----------------------------------------------------------------------------------------+
| Pipeline Input                                                                          |
+-----------------------------------------------------------------------------------------+
| Codebase Configuration                                                                  |
| Build Type:  ( ) Git Branch    (*) Commit SHA                                           |
| Commit SHA:  [ <+trigger.commitSha>                                                   ] |
|                                                                                         |
| Pipeline Variables                                                                      |
| dockerhub_username *: [ yourdockerhubusername                                         ] |
| dockerhub_repo_name:  [ employee-service                                              ] |
|                                                                                         |
|                                                              [Cancel]  [Create Trigger] |
+-----------------------------------------------------------------------------------------+
```

*Verification:* Harness will automatically call GitHub's API via `github_connector` and register a webhook in your GitHub repository (**Settings** ➔ **Webhooks**).

---

### 6.7 Running & Verifying the Pipeline

#### Manual Execution (First Test Run)
1. In your pipeline view, click the blue button in the top right: **`Run`**.
2. A **Run Pipeline** dialog will appear:

```
+-----------------------------------------------------------------+
| Run Pipeline                                                [X] |
+-----------------------------------------------------------------+
| Branch / Commit Tag: [ main                                   ] |
|                                                                 |
| Pipeline Variables:                                             |
| dockerhub_username *: [ yourdockerhubusername                ]  |
| dockerhub_repo_name:  [ employee-service                     ]  |
|                                                                 |
|                                                 [Cancel]  [Run] |
+-----------------------------------------------------------------+
```

3. Ensure your Git branch is selected (`main` or `master`).
4. In `dockerhub_username`, enter your Docker Hub username.
5. Click **Run Pipeline**.

#### Monitoring Execution & Viewing Logs
- Harness will transition to the live execution graph:
```
[Build and Verify Tests] ➔ ➔ ➔ [Containerize and Publish]
  - compile_source     [✓]       - build_and_push_docker_hub [✓]
  - run_unit_tests     [✓]
  - run_integration_tests [✓]
```
- Click on any step (e.g. `run_unit_tests`) to view real-time streaming console logs and JUnit test results.
- Upon completion, visit [hub.docker.com](https://hub.docker.com) to see your newly published image tagged with the exact Git commit SHA!

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
   # Example output: a9c01b3a02956ce70323863713491a88ea8d0201
   ```
3. Harness CI executes:
   - **Stage 1 (Build and Verify Tests):**
     - `compile_source` ➔ Succeeded.
     - `run_unit_tests` ➔ Succeeded (16 tests passed).
     - `run_integration_tests` ➔ Succeeded (5 integration tests passed).
   - **Stage 2 (Containerize and Publish):**
     - Step `build_and_push_docker_hub` builds the multi-stage Dockerfile.
     - Dynamic tags resolved:
       - `<username>/employee-service:<commitSha>` (Immutable SHA Tag)
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

| Issue / Error Symptom | Root Cause | Exact Low-Level Fix |
| :--- | :--- | :--- |
| `Cannot connect to Docker daemon` | Docker Desktop is not running on Windows 11. | Open Windows Start menu, click **Docker Desktop**, and wait for the status icon to turn green ("Engine running"). |
| `Connector github_connector not found` | The identifier in `pipeline.yaml` doesn't match the connector in Harness UI. | Go to **Project Settings** ➔ **Connectors**. Click on your GitHub connector, click the pencil edit icon next to Identifier, and ensure it is typed as `github_connector` (lowercase, underscore). |
| `Connector dockerhub_connector not found` | The identifier in `pipeline.yaml` doesn't match the connector in Harness UI. | Go to **Project Settings** ➔ **Connectors**. Ensure the Docker Hub connector identifier is exactly `dockerhub_connector`. |
| `denied: requested access to the resource is denied` during Docker push | Docker Hub token lacks write permissions or username mismatch. | 1. Go to hub.docker.com ➔ Account Settings ➔ Security. Create a new token with **Read, Write, Delete** permissions.<br>2. Update secret `dockerhub_token` in Harness.<br>3. Ensure `dockerhub_username` matches your account. |
| `Java 25 (69) is not supported by Byte Buddy` | ByteBuddy agent running on JDK 25 without experimental flag. | Ensure `-Dnet.bytebuddy.experimental=true` is present in the `mvn test` execution command (already configured in `pom.xml` surefire/failsafe plugin). |
| PowerShell argument parse error on `-D` flags | PowerShell treats `-Dproperty=value` as an operator. | Always wrap Java/Maven system properties in double quotes: `mvn test "-Dfail.ci.build=true"`. |
| Harness trigger does not fire on Git push | Webhook not registered in GitHub or branch mismatch. | 1. In GitHub, go to **Settings** ➔ **Webhooks**. Verify a webhook with Harness URL is present and shows a green checkmark.<br>2. Verify the branch in trigger condition matches your push branch (`main` vs `master`). |

---

## License & Attribution

Distributed under the Apache 2.0 License. Designed for DevOps engineers, SREs, and cloud architects learning enterprise CI/CD with Harness.
