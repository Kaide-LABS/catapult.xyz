# Penetration Test Summary

## 7.1 Vendor & Scope
The annual engagement was conducted by "SecureAudit Ltd". The scope included our external perimeter, web app, API, and mobile app.

## 7.2 Last Test Date
The last test was conducted in January 2026.

## 7.3 Findings
Findings breakdown: 0 Critical, 1 High (remediated in 7 days), 3 Medium (remediated in 30 days), and 5 Low.

## 7.4 High Finding Details
The single High finding was an IDOR vulnerability in the user profile API. It was fixed immediately via a server-side authz check.

## 7.5 Methodology & Re-test
Testing followed the OWASP Testing Guide v4.2 and PTES methodologies. A subsequent re-test confirmed all High and Medium findings were fully remediated.