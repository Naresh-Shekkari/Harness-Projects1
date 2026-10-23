package com.harness.demo.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.harness.demo.dto.EmployeeRequest;
import com.harness.demo.dto.EmployeeResponse;
import com.harness.demo.service.EmployeeService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.List;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(EmployeeController.class)
@DisplayName("Unit Tests - EmployeeController (WebMvc)")
class EmployeeControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private EmployeeService employeeService;

    @Test
    @DisplayName("GET /api/v1/health returns HTTP 200 with UP status")
    void getApiHealth_ReturnsOk() throws Exception {
        mockMvc.perform(get("/api/v1/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.service").value("employee-service"));
    }

    @Test
    @DisplayName("GET /api/v1/employees returns HTTP 200 with list of employees")
    void getAllEmployees_ReturnsList() throws Exception {
        EmployeeResponse employee = new EmployeeResponse(
                1L, "Margaret", "Hamilton", "margaret@example.com", "Software", 160000.0, Instant.now(), Instant.now()
        );

        when(employeeService.getAllEmployees()).thenReturn(List.of(employee));

        mockMvc.perform(get("/api/v1/employees"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].email").value("margaret@example.com"));
    }

    @Test
    @DisplayName("GET /api/v1/employees/{id} returns HTTP 200 when found")
    void getEmployeeById_ReturnsEmployee() throws Exception {
        EmployeeResponse employee = new EmployeeResponse(
                1L, "Margaret", "Hamilton", "margaret@example.com", "Software", 160000.0, Instant.now(), Instant.now()
        );

        when(employeeService.getEmployeeById(1L)).thenReturn(employee);

        mockMvc.perform(get("/api/v1/employees/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1L))
                .andExpect(jsonPath("$.firstName").value("Margaret"));
    }

    @Test
    @DisplayName("POST /api/v1/employees with valid body returns HTTP 201 Created")
    void createEmployee_Valid_ReturnsCreated() throws Exception {
        EmployeeRequest request = new EmployeeRequest(
                "Katherine", "Johnson", "katherine@example.com", "Mathematics", 155000.0
        );

        EmployeeResponse created = new EmployeeResponse(
                50L, "Katherine", "Johnson", "katherine@example.com", "Mathematics", 155000.0, Instant.now(), Instant.now()
        );

        when(employeeService.createEmployee(any(EmployeeRequest.class))).thenReturn(created);

        mockMvc.perform(post("/api/v1/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", containsString("/api/v1/employees/50")))
                .andExpect(jsonPath("$.id").value(50L))
                .andExpect(jsonPath("$.email").value("katherine@example.com"));
    }

    @Test
    @DisplayName("POST /api/v1/employees with invalid body returns HTTP 400 Bad Request with field errors")
    void createEmployee_Invalid_ReturnsBadRequest() throws Exception {
        // Missing required fields and bad email format
        EmployeeRequest invalidRequest = new EmployeeRequest(
                "", "", "invalid-email-string", "", -100.0
        );

        mockMvc.perform(post("/api/v1/employees")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.validationErrors.firstName").exists())
                .andExpect(jsonPath("$.validationErrors.email").exists())
                .andExpect(jsonPath("$.validationErrors.salary").exists());
    }

    @Test
    @DisplayName("DELETE /api/v1/employees/{id} returns HTTP 204 No Content")
    void deleteEmployee_ReturnsNoContent() throws Exception {
        doNothing().when(employeeService).deleteEmployee(10L);

        mockMvc.perform(delete("/api/v1/employees/10"))
                .andExpect(status().isNoContent());
    }
}
