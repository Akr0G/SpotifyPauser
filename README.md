# Spotify Pauser (YouTube-Aware Audio Control)
A real-time automation tool that mutes Spotify when YouTube is active and restores audio when focus changes — enhancing multitasking and media clarity.

## Overview
This project showcases intelligent desktop automation through seamless system-level integration. Designed to improve user experience while multitasking, the tool prevents audio overlap by monitoring active windows and dynamically muting/unmuting Spotify based on YouTube focus.

**Note:** This repository is private and intended for demonstration purposes only.

## Features
- Automatically mutes Spotify when a YouTube tab is focused  
- Unmutes Spotify when the user navigates away from YouTube  
- Context-aware logic using window title and process state detection  
- Native Windows notifications with cooldown to avoid spam  
- Robust logging for behavior tracking and debugging  

## Tech Stack
- **Language:** Python 3  
- **Libraries:**  
  - `pycaw` (Windows Core Audio API)  
  - `pygetwindow` + `win32gui` (Window detection)  
  - `psutil` (Process monitoring)  
  - `plyer` (System notifications)  
  - `logging` (Persistent event logs)  
- **Platform:** Windows  
- **Tools:** Git, GitHub, VS Code  

## My Contributions
- Built full logic for detecting Spotify’s playback state via system audio sessions  
- Engineered active window focus detection with support for multiple browsers  
- Designed thread-safe muting logic with caching and error resilience  
- Implemented a notification system with cooldown to ensure smooth UX  
- Managed comprehensive logging for all core actions and exceptions  

## Demo
Demo video or screenshots available upon request. Please contact me to preview the tool in action.

## Access
If you're a college admissions officer, recruiter, or reviewer and would like access to the code, feel free to reach out. I’ll provide collaborator access upon request.

## Contact
**Email:** [gajula.akhil13@gmail.com]  
**GitHub:** [https://github.com/Akr0G]
