# Quick Start Guide

## HeyReach Dashboard

**Command to run:**
```bash
python app.py
```

**Or use the script:**
- Windows: `run_dashboard.bat`
- Linux/Mac: `run_dashboard.sh`

**Browser link:**
http://localhost:5000

---

## Task Manager

**Command to run:**
```bash
cd task_manager
python task_manager.py
```

**Or use the script:**
- Windows: `cd task_manager && run_task_manager.bat`
- Linux/Mac: `cd task_manager && ./run_task_manager.sh`

**Browser link:**
http://localhost:5001/tasks

---

## Running Both Simultaneously

You can run both applications at the same time since they use different ports:
- HeyReach Dashboard: Port 5000
- Task Manager: Port 5001

Open two terminal windows:
1. Terminal 1: `python app.py` (HeyReach Dashboard)
2. Terminal 2: `cd task_manager && python task_manager.py` (Task Manager)
