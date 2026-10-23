package com.harness.demo.service;

import com.harness.demo.dto.EmployeeRequest;
import com.harness.demo.dto.EmployeeResponse;
import com.harness.demo.exception.DuplicateResourceException;
import com.harness.demo.exception.ResourceNotFoundException;
import com.harness.demo.model.Employee;
import com.harness.demo.repository.EmployeeRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("Unit Tests - EmployeeService")
class EmployeeServiceTest {

    @Mock
    private EmployeeRepository repository;

    @InjectMocks
    private EmployeeService employeeService;

    private Employee sampleEmployee;
    private EmployeeRequest sampleRequest;

    @BeforeEach
    void setUp() {
        sampleEmployee = new Employee(
                101L,
                "Ada",
                "Lovelace",
                "ada@example.com",
                "Algorithms",
                140000.0,
                Instant.now(),
                Instant.now()
        );

        sampleRequest = new EmployeeRequest(
                "Ada",
                "Lovelace",
                "ada@example.com",
                "Algorithms",
                140000.0
        );
    }

    @Test
    @DisplayName("getAllEmployees should return all mapped employees")
    void getAllEmployees_Success() {
        when(repository.findAll()).thenReturn(List.of(sampleEmployee));

        List<EmployeeResponse> result = employeeService.getAllEmployees();

        assertThat(result).hasSize(1);
        assertThat(result.getFirst().email()).isEqualTo("ada@example.com");
        verify(repository, times(1)).findAll();
    }

    @Test
    @DisplayName("getEmployeeById should return employee when ID exists")
    void getEmployeeById_Found() {
        when(repository.findById(101L)).thenReturn(Optional.of(sampleEmployee));

        EmployeeResponse response = employeeService.getEmployeeById(101L);

        assertThat(response.id()).isEqualTo(101L);
        assertThat(response.firstName()).isEqualTo("Ada");
        verify(repository, times(1)).findById(101L);
    }

    @Test
    @DisplayName("getEmployeeById should throw ResourceNotFoundException when ID does not exist")
    void getEmployeeById_NotFound() {
        when(repository.findById(999L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> employeeService.getEmployeeById(999L))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("999");

        verify(repository, times(1)).findById(999L);
    }

    @Test
    @DisplayName("createEmployee should save and return response when email is unique")
    void createEmployee_Success() {
        when(repository.findByEmail(sampleRequest.email())).thenReturn(Optional.empty());
        when(repository.save(any(Employee.class))).thenReturn(sampleEmployee);

        EmployeeResponse created = employeeService.createEmployee(sampleRequest);

        assertThat(created.id()).isEqualTo(101L);
        assertThat(created.email()).isEqualTo("ada@example.com");
        verify(repository).findByEmail(sampleRequest.email());
        verify(repository).save(any(Employee.class));
    }

    @Test
    @DisplayName("createEmployee should throw DuplicateResourceException when email is already taken")
    void createEmployee_DuplicateEmail() {
        when(repository.findByEmail(sampleRequest.email())).thenReturn(Optional.of(sampleEmployee));

        assertThatThrownBy(() -> employeeService.createEmployee(sampleRequest))
                .isInstanceOf(DuplicateResourceException.class)
                .hasMessageContaining("already exists");

        verify(repository, never()).save(any(Employee.class));
    }

    @Test
    @DisplayName("updateEmployee should update existing record when inputs are valid")
    void updateEmployee_Success() {
        when(repository.findById(101L)).thenReturn(Optional.of(sampleEmployee));
        when(repository.findByEmail(sampleRequest.email())).thenReturn(Optional.of(sampleEmployee));
        when(repository.save(any(Employee.class))).thenReturn(sampleEmployee);

        EmployeeResponse updated = employeeService.updateEmployee(101L, sampleRequest);

        assertThat(updated.id()).isEqualTo(101L);
        verify(repository).save(any(Employee.class));
    }

    @Test
    @DisplayName("updateEmployee should throw DuplicateResourceException if updated email belongs to someone else")
    void updateEmployee_ConflictEmail() {
        Employee anotherEmployee = new Employee(
                202L, "Grace", "Hopper", "grace@example.com", "Compilers", 150000.0, Instant.now(), Instant.now()
        );

        when(repository.findById(101L)).thenReturn(Optional.of(sampleEmployee));
        when(repository.findByEmail(sampleRequest.email())).thenReturn(Optional.of(anotherEmployee));

        assertThatThrownBy(() -> employeeService.updateEmployee(101L, sampleRequest))
                .isInstanceOf(DuplicateResourceException.class)
                .hasMessageContaining("already in use");

        verify(repository, never()).save(any(Employee.class));
    }

    @Test
    @DisplayName("deleteEmployee should delete record when ID exists")
    void deleteEmployee_Success() {
        when(repository.existsById(101L)).thenReturn(true);

        employeeService.deleteEmployee(101L);

        verify(repository).deleteById(101L);
    }

    @Test
    @DisplayName("deleteEmployee should throw ResourceNotFoundException when ID does not exist")
    void deleteEmployee_NotFound() {
        when(repository.existsById(999L)).thenReturn(false);

        assertThatThrownBy(() -> employeeService.deleteEmployee(999L))
                .isInstanceOf(ResourceNotFoundException.class);

        verify(repository, never()).deleteById(anyLong());
    }
}
