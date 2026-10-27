# M.Tech Dissertation Draft Content

## Title
Intelligent Linux Infrastructure Monitoring and Predictive Alerting System

## Abstract
Modern organizations operate large numbers of Linux servers that host databases, middleware, web applications and enterprise services. Manual health checks become time-consuming and can delay detection of resource exhaustion. This project presents a web-based infrastructure monitoring system that centralizes Linux server health information. A lightweight Python agent collects CPU, memory, disk, load and uptime information and sends the metrics to a central Flask REST API. The backend stores historical measurements in SQLite and evaluates resource thresholds to classify servers as Healthy, Warning or Critical. A browser-based dashboard provides a consolidated view of server inventory and alerts. The design is modular so that PostgreSQL, authentication, enterprise notifications, URL checks and predictive analytics can be added in future work.

## Problem Statement
Manual infrastructure checks require repeated login and command execution across many servers. The absence of a centralized view can increase detection and response time.

## Objectives
1. Centralize Linux server health monitoring.
2. Reduce manual effort in routine health checks.
3. Provide threshold-based alerting.
4. Maintain historical metric records.
5. Provide a simple browser dashboard.
6. Create an extensible foundation for predictive infrastructure analytics.

## Methodology
The system follows an agent-to-server architecture. A lightweight monitoring agent runs on monitored Linux hosts. It uses operating-system metrics to collect resource information and transmits JSON to a central REST API. The backend validates the data, stores the metrics and computes health status. The dashboard retrieves current data through REST endpoints.

## Architecture
Linux servers -> Monitoring Agent -> REST API -> Database -> Dashboard -> Alerts.

## Modules
1. Monitoring Agent
2. REST API
3. Database
4. Health Evaluation Engine
5. Alert Module
6. Web Dashboard
7. Simulation/Test Module

## Health Score
The prototype uses:
Score = 100 - (0.4*CPU + 0.3*Memory + 0.3*Disk)
The result is bounded between 0 and 100. This is a project-defined operational indicator, not a standard industry metric.

## Threshold Logic
- Healthy: maximum CPU/RAM/Disk below 80%
- Warning: maximum resource between 80% and below 90%
- Critical: maximum resource at or above 90%

## Advantages
- Centralized visibility
- Reduced manual effort
- Simple deployment
- Historical data
- Extensible REST architecture
- Suitable for Linux administration workflows

## Limitations
- Current prototype uses SQLite.
- Thresholds are static.
- Ingestion endpoint needs authentication and TLS for production.
- Predictive analytics is an extension rather than part of the base prototype.

## Future Scope
- PostgreSQL/TimescaleDB
- Role-based access control
- TLS and signed agent authentication
- Email/Teams/SMS alerts
- URL and TCP port monitoring
- Anomaly detection
- Disk growth forecasting
- Automated remediation
- Ansible-based fleet deployment
- High availability for monitoring backend

## Expected Result
The system should provide a consolidated view of Linux server health and identify resource conditions requiring attention, reducing dependence on manual command-by-command checks.
