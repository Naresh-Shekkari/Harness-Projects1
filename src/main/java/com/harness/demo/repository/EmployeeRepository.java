package com.harness.demo.repository;

import com.harness.demo.model.Employee;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Repository
public class EmployeeRepository {

    private final ConcurrentHashMap<Long, Employee> store = new ConcurrentHashMap<>();
    private final AtomicLong idSequence = new AtomicLong(1000);

    public EmployeeRepository() {
        // Seed default production-like records for out-of-the-box demonstration
        save(new Employee(null, "Sarah", "Connor", "sarah.connor@example.com", "DevOps", 125000.0, null, null));
        save(new Employee(null, "John", "Doe", "john.doe@example.com", "Engineering", 110000.0, null, null));
        save(new Employee(null, "Alex", "Murphy", "alex.murphy@example.com", "Security", 135000.0, null, null));
    }

    public List<Employee> findAll() {
        return new ArrayList<>(store.values());
    }

    public Optional<Employee> findById(Long id) {
        return Optional.ofNullable(store.get(id));
    }

    public Optional<Employee> findByEmail(String email) {
        if (email == null) return Optional.empty();
        return store.values().stream()
                .filter(e -> email.equalsIgnoreCase(e.getEmail()))
                .findFirst();
    }

    public Employee save(Employee employee) {
        Instant now = Instant.now();
        if (employee.getId() == null) {
            employee.setId(idSequence.incrementAndGet());
            employee.setCreatedAt(now);
            employee.setUpdatedAt(now);
        } else {
            employee.setUpdatedAt(now);
        }
        store.put(employee.getId(), employee);
        return employee;
    }

    public boolean deleteById(Long id) {
        return store.remove(id) != null;
    }

    public boolean existsById(Long id) {
        return store.containsKey(id);
    }

    public void clear() {
        store.clear();
    }
}
