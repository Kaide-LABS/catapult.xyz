# Business Continuity Plan

## 6.1 RTO and RPO
Our Recovery Time Objective (RTO) is 4 hours for critical systems and 24 hours for non-critical systems. The Recovery Point Objective (RPO) is 1 hour for databases and 24 hours for file storage.

## 6.2 Backup Strategies
We enforce daily automated snapshots, cross-region replication, and conduct monthly restore tests.

## 6.3 Disaster Recovery Site
Our primary region is AWS us-east-1, with an automated DR site in AWS eu-west-1. Failover is managed via Route 53.

## 6.4 Testing
We perform a full DR exercise annually and tabletop exercises quarterly.

## 6.5 Communication Tree
The escalation tree is: CEO > CTO > VP Eng > SRE Lead. Customer updates are posted to our public status page.