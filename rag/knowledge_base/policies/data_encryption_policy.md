# Data Encryption Policy

## 2.1 Encryption At-rest
All data stored persistently is protected using AES-256-GCM via AWS KMS. Customers may opt for customer-managed keys (CMK) for dedicated environments.

## 2.2 Encryption In-transit
TLS 1.3 is mandatory for all external and internal communications. Certificate pinning is enforced for our mobile application. We enforce HSTS headers across all web properties.

## 2.3 Key Management
Cryptographic keys are subject to a 90-day rotation schedule. We enforce split-knowledge custodians for manual key recovery operations. All production keys are HSM-backed.

## 2.4 Database Encryption
Column-level encryption is applied for all PII fields within our databases. We employ an envelope encryption pattern to ensure data keys are protected by master keys.