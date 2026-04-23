package com.microservice.gateway.config;

import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "app.security")
public class GatewaySecurityProperties {

    private boolean enabled = false;

    @NotBlank
    private String jwtSecret = "change-me-change-me-change-me-change-me";

    private String tenantClaim = "tenant_id";
    private String roleClaim = "roles";
    private String devUserId = "dev-user";
    private String devTenantId = "dev-tenant";
    private String devRoles = "ROLE_ADMIN";

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public String getJwtSecret() {
        return jwtSecret;
    }

    public void setJwtSecret(String jwtSecret) {
        this.jwtSecret = jwtSecret;
    }

    public String getTenantClaim() {
        return tenantClaim;
    }

    public void setTenantClaim(String tenantClaim) {
        this.tenantClaim = tenantClaim;
    }

    public String getRoleClaim() {
        return roleClaim;
    }

    public void setRoleClaim(String roleClaim) {
        this.roleClaim = roleClaim;
    }

    public String getDevUserId() {
        return devUserId;
    }

    public void setDevUserId(String devUserId) {
        this.devUserId = devUserId;
    }

    public String getDevTenantId() {
        return devTenantId;
    }

    public void setDevTenantId(String devTenantId) {
        this.devTenantId = devTenantId;
    }

    public String getDevRoles() {
        return devRoles;
    }

    public void setDevRoles(String devRoles) {
        this.devRoles = devRoles;
    }
}
