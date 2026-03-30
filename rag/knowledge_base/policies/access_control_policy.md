# Access Control Policy

## 4.1 RBAC Roles
Access is governed by strict RBAC utilizing 4 predefined roles: Admin, Engineer, Analyst, and Viewer.

## 4.2 Authentication
MFA is mandatory for all personnel. Supported methods include TOTP or hardware security keys (FIDO2/WebAuthn). We enforce SSO via SAML 2.0 / OIDC, fully integrated with Okta.

## 4.3 Session Management
Application sessions enforce a 30-minute idle timeout and a 12-hour absolute timeout.

## 4.4 Least Privilege
We mandate quarterly access reviews to enforce the principle of least privilege. JIT (Just-In-Time) access is required for any interaction with production systems.

## 4.5 Audit Logging
All access events are streamed to an immutable log store with a strict 1-year retention policy.