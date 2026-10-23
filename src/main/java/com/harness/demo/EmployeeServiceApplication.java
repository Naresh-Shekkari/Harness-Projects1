package com.harness.demo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class EmployeeServiceApplication {

    private static final Logger log = LoggerFactory.getLogger(EmployeeServiceApplication.class);

    public static void main(String[] args) {
        log.info("Starting Employee Management Service on Java {} ...", System.getProperty("java.version"));
        SpringApplication.run(EmployeeServiceApplication.class, args);
        log.info("Employee Management Service started successfully.");
    }
}
