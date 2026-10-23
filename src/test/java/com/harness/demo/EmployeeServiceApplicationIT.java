package com.harness.demo;

import com.harness.demo.dto.EmployeeRequest;
import com.harness.demo.dto.EmployeeResponse;
import com.harness.demo.dto.ErrorResponse;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DisplayName("Integration Tests - Full Spring Boot Application Stack (Failsafe)")
class EmployeeServiceApplicationIT {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    private String getBaseUrl() {
        return "http://localhost:" + port;
    }

    @Test
    @DisplayName("IT: Spring Boot Actuator /actuator/health returns UP")
    void actuatorHealth_ReturnsUp() {
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                getBaseUrl() + "/actuator/health",
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<>() {}
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        Map<String, Object> body = Objects.requireNonNull(response.getBody(), "Health body must not be null");
        assertThat(body.get("status")).isEqualTo("UP");
    }

    @Test
    @DisplayName("IT: Correlation ID is propagated in response headers")
    void correlationId_PropagatedSuccessfully() {
        String customCorrelationId = "test-corr-" + UUID.randomUUID();
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Correlation-Id", customCorrelationId);

        HttpEntity<Void> request = new HttpEntity<>(headers);
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                getBaseUrl() + "/api/v1/health",
                HttpMethod.GET,
                request,
                new ParameterizedTypeReference<>() {}
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getHeaders().getFirst("X-Correlation-Id")).isEqualTo(customCorrelationId);
    }

    @Test
    @DisplayName("IT: End-to-End CRUD Lifecycle Flow")
    void fullEmployeeCrudLifecycle() {
        // 1. Initial listing contains seeded records
        ResponseEntity<List<EmployeeResponse>> listResponse = restTemplate.exchange(
                getBaseUrl() + "/api/v1/employees",
                HttpMethod.GET,
                null,
                new ParameterizedTypeReference<>() {}
        );
        assertThat(listResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        List<EmployeeResponse> initialList = Objects.requireNonNull(listResponse.getBody(), "Initial list cannot be null");
        assertThat(initialList).isNotEmpty();

        // 2. Create a new employee
        EmployeeRequest createRequest = new EmployeeRequest(
                "Linus", "Torvalds", "linus.torvalds@kernel.org", "Kernel", 200000.0
        );
        ResponseEntity<EmployeeResponse> createResponse = restTemplate.postForEntity(
                getBaseUrl() + "/api/v1/employees",
                createRequest,
                EmployeeResponse.class
        );

        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        EmployeeResponse created = Objects.requireNonNull(createResponse.getBody(), "Created response body must not be null");
        assertThat(created.id()).isNotNull();
        assertThat(created.email()).isEqualTo("linus.torvalds@kernel.org");

        Long employeeId = created.id();

        // 3. Read the created employee by ID
        ResponseEntity<EmployeeResponse> getResponse = restTemplate.getForEntity(
                getBaseUrl() + "/api/v1/employees/" + employeeId,
                EmployeeResponse.class
        );
        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        EmployeeResponse fetched = Objects.requireNonNull(getResponse.getBody(), "Fetched employee must not be null");
        assertThat(fetched.firstName()).isEqualTo("Linus");

        // 4. Update the employee's salary and department
        EmployeeRequest updateRequest = new EmployeeRequest(
                "Linus", "Torvalds", "linus.torvalds@kernel.org", "Linux Foundation", 220000.0
        );
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<EmployeeRequest> updateEntity = new HttpEntity<>(updateRequest, headers);

        ResponseEntity<EmployeeResponse> updateResponse = restTemplate.exchange(
                getBaseUrl() + "/api/v1/employees/" + employeeId,
                HttpMethod.PUT,
                updateEntity,
                EmployeeResponse.class
        );
        assertThat(updateResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        EmployeeResponse updated = Objects.requireNonNull(updateResponse.getBody(), "Updated response body must not be null");
        assertThat(updated.department()).isEqualTo("Linux Foundation");
        assertThat(updated.salary()).isEqualTo(220000.0);

        // 5. Delete the employee
        ResponseEntity<Void> deleteResponse = restTemplate.exchange(
                getBaseUrl() + "/api/v1/employees/" + employeeId,
                HttpMethod.DELETE,
                null,
                Void.class
        );
        assertThat(deleteResponse.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);

        // 6. Verify that fetching the deleted employee returns 404
        ResponseEntity<ErrorResponse> notFoundResponse = restTemplate.getForEntity(
                getBaseUrl() + "/api/v1/employees/" + employeeId,
                ErrorResponse.class
        );
        assertThat(notFoundResponse.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test
    @DisplayName("IT: Attempting to create duplicate email returns 409 Conflict")
    void createDuplicateEmail_ReturnsConflict() {
        EmployeeRequest request = new EmployeeRequest(
                "Duplicate", "Test", "sarah.connor@example.com", "QA", 90000.0
        );

        ResponseEntity<ErrorResponse> response = restTemplate.postForEntity(
                getBaseUrl() + "/api/v1/employees",
                request,
                ErrorResponse.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
        ErrorResponse error = Objects.requireNonNull(response.getBody(), "Conflict response body must not be null");
        assertThat(error.message()).contains("already exists");
    }

    @Test
    @DisplayName("IT: Submitting invalid payload returns 400 Bad Request with validation errors")
    void createInvalidEmployee_ReturnsBadRequest() {
        EmployeeRequest invalidRequest = new EmployeeRequest(
                "", "", "not-an-email", "", -50.0
        );

        ResponseEntity<ErrorResponse> response = restTemplate.postForEntity(
                getBaseUrl() + "/api/v1/employees",
                invalidRequest,
                ErrorResponse.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        ErrorResponse error = Objects.requireNonNull(response.getBody(), "Bad request body must not be null");
        assertThat(error.validationErrors()).isNotEmpty();
    }
}
