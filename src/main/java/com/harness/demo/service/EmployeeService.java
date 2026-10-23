package com.harness.demo.service;

import com.harness.demo.dto.EmployeeRequest;
import com.harness.demo.dto.EmployeeResponse;
import com.harness.demo.exception.DuplicateResourceException;
import com.harness.demo.exception.ResourceNotFoundException;
import com.harness.demo.model.Employee;
import com.harness.demo.repository.EmployeeRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class EmployeeService {

    private static final Logger log = LoggerFactory.getLogger(EmployeeService.class);

    private final EmployeeRepository repository;

    public EmployeeService(EmployeeRepository repository) {
        this.repository = repository;
    }

    public List<EmployeeResponse> getAllEmployees() {
        log.info("Fetching all employees from repository");
        return repository.findAll().stream()
                .map(EmployeeResponse::fromEntity)
                .toList();
    }

    public EmployeeResponse getEmployeeById(Long id) {
        log.info("Fetching employee with id: {}", id);
        Employee employee = repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Employee with id " + id + " not found"));
        return EmployeeResponse.fromEntity(employee);
    }

    public EmployeeResponse createEmployee(EmployeeRequest request) {
        log.info("Creating employee with email: {}", request.email());

        repository.findByEmail(request.email()).ifPresent(existing -> {
            throw new DuplicateResourceException("Employee with email '" + request.email() + "' already exists");
        });

        Employee employee = new Employee(
                null,
                request.firstName().trim(),
                request.lastName().trim(),
                request.email().trim().toLowerCase(),
                request.department().trim(),
                request.salary(),
                null,
                null
        );

        Employee saved = repository.save(employee);
        log.info("Successfully created employee with id: {}", saved.getId());
        return EmployeeResponse.fromEntity(saved);
    }

    public EmployeeResponse updateEmployee(Long id, EmployeeRequest request) {
        log.info("Updating employee id: {}", id);

        Employee employee = repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Employee with id " + id + " not found"));

        repository.findByEmail(request.email()).ifPresent(existing -> {
            if (!existing.getId().equals(id)) {
                throw new DuplicateResourceException("Email '" + request.email() + "' is already in use by another employee");
            }
        });

        employee.setFirstName(request.firstName().trim());
        employee.setLastName(request.lastName().trim());
        employee.setEmail(request.email().trim().toLowerCase());
        employee.setDepartment(request.department().trim());
        employee.setSalary(request.salary());

        Employee updated = repository.save(employee);
        log.info("Successfully updated employee with id: {}", updated.getId());
        return EmployeeResponse.fromEntity(updated);
    }

    public void deleteEmployee(Long id) {
        log.info("Deleting employee with id: {}", id);
        if (!repository.existsById(id)) {
            throw new ResourceNotFoundException("Employee with id " + id + " not found");
        }
        repository.deleteById(id);
        log.info("Successfully deleted employee with id: {}", id);
    }
}
