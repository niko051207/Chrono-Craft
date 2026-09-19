# Master Context: Chrono-Craft (Pygame Project)

## 1. Project Overview
- **Title:** Chrono-Craft
- **Engine:** Python 3 + Pygame (Standard library only, no extra game engines).
- **Genre:** Tactical Deckbuilder meets Real-Time Physics Simulation.
- **Core Loop:** 
  1. **Planning Phase (Turn-based):** Time is paused. Player selects action cards (e.g., Dash, Push, Time-Slow) from a deck and places them into a timeline queue.
  2. **Action Phase (Real-time):** The timeline executes. Physics (velocity, collisions, impulses) run in real-time for a set duration (e.g., 3-5 seconds).
- **Visual Style:** Retro Pixel-Art.

## 2. Technical Standards & Rules for AI (STRICT)
As an AI assisting with this project, you must strictly adhere to the following rules to ensure the codebase remains maintainable, bug-free, and computationally efficient:

- **Resolution Scaling:** The game must be rendered on a small internal `pygame.Surface` (e.g., 480x270) and then scaled up to the main display window (e.g., 1280x720) using `pygame.transform.scale()` to achieve a crisp pixel-art look.
- **Delta Time (dt):** All movement, physics, and timers MUST be multiplied by `dt` to ensure frame-rate independence.
- **Vector Math:** Use `pygame.math.Vector2` exclusively for position, velocity, and acceleration.
- **Algorithmic Efficiency:** The user has a strong foundation in data structures, algorithms, and computational logic. Ensure the state management and physics collision logic utilize efficient approaches (e.g., appropriate use of queues for the card timeline, FSM for game states) rather than brute-force loops.
- **Modular OOP:** Do NOT put everything in one file. Separate logic strictly into the predefined module structure below.

## 3. Directory & Module Structure
The project is divided into the following files. When generating code, always specify which file you are editing.

- `main.py`: Entry point. Handles the Pygame event loop, `dt` calculation, scaling the internal surface to the screen, and routing the current game state.
- `settings.py`: Contains global constants (SCREEN_WIDTH, SCREEN_HEIGHT, INTERNAL_WIDTH, INTERNAL_HEIGHT, FPS, COLORS, PHYSICS_GRAVITY, etc.).
- `state_manager.py`: Implements a Finite State Machine (FSM) to cleanly toggle between `PLANNING_PHASE` and `ACTION_PHASE`.
- `physics_engine.py`: Contains the `Entity` base class. Handles Vector2 math, AABB/Circle collisions, friction, bounce (restitution), and applying forces (impulses).
- `card_system.py`: Manages the `Card` class, deck initialization, the timeline queue, and mapping card effects to physics impulses on entities.
- `ui_renderer.py`: Handles drawing the cards, timeline, and text over the main game surface.

## 4. Vibecoding Protocol
When asked to implement a feature:
1. Briefly state the plan and which files will be affected.
2. Provide only the necessary code blocks to implement the feature. Do not output the entire file unless it is requested or if it's the first initialization.
3. Keep methods small and focused. Leave comments explaining complex vector math or state transitions.