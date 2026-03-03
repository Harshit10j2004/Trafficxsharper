# TrafficXShaper V2

ML-Powered Auto-Scaling for Docker Swarm on AWS

TrafficShaprX is a sophisticated auto-scaling system that combines real-time metrics collection, machine learning predictions, and intelligent node management to automatically scale your Docker Swarm cluster based on actual load conditions.


# ✨ Features

**📊 Intelligent Scaling**

ML-Powered Predictions: Random Forest models predict future CPU usage

Multiple Triggers: CPU spikes, queue pressure, and ML predictions

Per-Client Models: Individual models for different workloads

Gray Zone Detection: ML kicks in when metrics are ambiguous

**🔄 Complete Lifecycle Management**

Auto-Join: New instances automatically join the Swarm

Graceful Draining: Nodes drain safely before removal

Self-Draining: Underutilized nodes initiate scale-down

Safety Checks: Verifies cluster capacity before removal

**🛡️ Production-Ready**

Cooldown Periods: Prevents scaling thrashing (300s up / 240s down)

Timestamp Validation: 60s skew tolerance

State Persistence: SQLite for resilience across restarts

Missing Node Detection: Alerts when nodes stop reporting

**📧 Alerting & Monitoring**

Email Notifications: All scaling events via SMTP (Gmail)

Comprehensive Logging: Request IDs for traceability

Metrics Collection: System and Nginx metrics

# 🎯 The Problem

Docker Swarm has no built-in auto-scaling. Period.

If you run Swarm in production today:

You scale manually (docker service scale web=10)

You build custom scripts that probably break

You over-provision "just in case" and waste money

You get paged at 3 AM when traffic spikes

TrafficShaprX fixes this. It's a working system we built and use.

✅ What's HERE (Working Now)
1. Data Collection (Bash scripts on every node)
collector.sh - CPU, memory, disk, network I/O every 10 seconds

nginx-collector.sh - Nginx connection stats (active, reading, writing, waiting)

Sends via netcat to aggregator (ports 9000/9001)

2. Aggregator (Python)
Reads all node logs

Averages metrics across cluster

Calculates: RPS, connection rate, queue pressure

Detects missing nodes

POSTs to Broker API

3. Broker API (FastAPI - Port 8000)
Receives metrics at /ingest

Validates timestamp (<60s skew)

Maintains state in SQLite (/home/ubuntu/tsx/data/client_data.db)

3 actual scaling triggers that work:

python
# Trigger 1: CPU spike
if total_cpu_window >= 3 and not in_cooldown:
    scaling("UP")  # Launches EC2 instances

# Trigger 2: App pressure
if queue_increasing >= 3 and rps_increasing >= 3:
    scaling("UP")  # Launches EC2 instances

# Trigger 3: ML prediction
if new_cur_ml >= 3:
    scaling("ML")  # Launches EC2 instances
4. ML Service (FastAPI - Port 8001)
/insert - Stores metrics for training

/clean - Returns CPU prediction using Random Forest

Features: 5 lags, rolling stats, deltas

Needs at least 6 data points to predict

5. Decision Engine (FastAPI - Port 8002)
/deceng - Launches EC2 instances with user-data that auto-joins Swarm

/deceng_down - Terminates instances

Tracks pending/joined in text files

6. Manager API (FastAPI - Port 8003 - runs on Swarm manager)
/manager - Approves node removal only if:

Other nodes exist

Other nodes aren't overloaded (<65% CPU/mem)

Then drains node and waits up to 900s

7. Self-Draining Agent (Bash - runs on every node)
Monitors local CPU

If CPU < 20% for 3 cycles (30 seconds):

Asks Manager API for approval

If approved: drains itself, leaves swarm, triggers termination

8. Alert Service (FastAPI - Port 8004)
/email - Sends Gmail alerts for scaling events



📋 Prerequisites

Infrastructure
AWS Account with EC2 permissions

Docker Swarm cluster (manager and worker nodes)

Ubuntu 20.04/22.04 on all nodes

MySQL database for persistent configuration

SMTP credentials (Gmail recommended)