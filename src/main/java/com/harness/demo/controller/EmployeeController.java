package com.harness.demo.controller;

import com.harness.demo.dto.EmployeeRequest;
import com.harness.demo.dto.EmployeeResponse;
import com.harness.demo.service.EmployeeService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1")
public class EmployeeController {

    private static final Logger log = LoggerFactory.getLogger(EmployeeController.class);

    private final EmployeeService employeeService;

    public EmployeeController(EmployeeService employeeService) {
        this.employeeService = employeeService;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> getApiHealth() {
        return ResponseEntity.ok(Map.of(
                "status", "UP",
                "service", "employee-service",
                "timestamp", Instant.now().toString(),
                "javaVersion", System.getProperty("java.version")
        ));
    }

    @GetMapping("/employees")
    public ResponseEntity<List<EmployeeResponse>> getAllEmployees() {
        log.info("REST request to get all employees");
        return ResponseEntity.ok(employeeService.getAllEmployees());
    }

    @GetMapping("/employees/{id}")
    public ResponseEntity<EmployeeResponse> getEmployeeById(@PathVariable Long id) {
        log.info("REST request to get employee id={}", id);
        return ResponseEntity.ok(employeeService.getEmployeeById(id));
    }

    @PostMapping("/employees")
    public ResponseEntity<EmployeeResponse> createEmployee(@Valid @RequestBody EmployeeRequest request) {
        log.info("REST request to create employee: email={}", request.email());
        EmployeeResponse created = employeeService.createEmployee(request);

        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{id}")
                .buildAndExpand(created.id())
                .toUri();

        return ResponseEntity.created(location).body(created);
    }

    @PutMapping("/employees/{id}")
    public ResponseEntity<EmployeeResponse> updateEmployee(
            @PathVariable Long id,
            @Valid @RequestBody EmployeeRequest request) {
        log.info("REST request to update employee id={}", id);
        return ResponseEntity.ok(employeeService.updateEmployee(id, request));
    }
    // new line added

    @DeleteMapping("/employees/{id}")
    public ResponseEntity<Void> deleteEmployee(@PathVariable Long id) {
        log.info("REST request to delete employee id={}", id);
        employeeService.deleteEmployee(id);
        return ResponseEntity.noContent().build();
    }
}

// included new pipelines for checking