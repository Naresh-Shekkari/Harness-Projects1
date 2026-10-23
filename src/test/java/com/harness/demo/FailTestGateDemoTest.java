package com.harness.demo;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.fail;

@DisplayName("Test Failure Gate Verification (Harness CI Safety Proof)")
class FailTestGateDemoTest {

    @Test
    @DisplayName("Verify CI test gate halts build when -Dfail.ci.build=true is supplied")
    void testFailureGateDemonstration() {
        String shouldFail = System.getProperty("fail.ci.build", "false");
        if (Boolean.parseBoolean(shouldFail)) {
            fail("PROVING CI FAILURE GATE: System property 'fail.ci.build' was set to true. " +
                 "Maven build is terminated immediately, preventing artifact packaging and container publication.");
        }
        assertThat(true).isTrue();
    }
}
